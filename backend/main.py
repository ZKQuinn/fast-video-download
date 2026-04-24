"""
Fast Video Download - 后端服务
版权所有 © 2024 保留所有权利

[合规与免责声明]
本项目仅用于技术学习和研究目的。请用户仅下载自己拥有版权或已获得合法授权的内容。
用户应自行遵守所在地区的法律法规及各平台的服务条款。使用即表示您同意自行承担所有法律后果。

Copyright © 2024 All Rights Reserved.
[Compliance & Disclaimer]
This project is for technical learning and research purposes only. 
Please only download content you own or have legal authorization for. 
Users are responsible for complying with local laws and platform terms.
"""
import asyncio
import os
import shutil
import sys
import time
import re
from typing import Optional, Any
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
import httpx
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from downloader import VideoDownloader
from douyin import DouyinParser
from app.agent.orchestrator import run as run_app_agent
from app.download_tasks import (
    complete_download_task,
    create_download_task,
    fail_download_task,
    task_status,
    update_download_progress,
)
import models
from database import engine, Base, get_db
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user,
    get_current_user_optional,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, datetime, timedelta
import stripe

# 常量与配置
BASE_DIR = os.path.dirname(__file__)
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")  # 在 .env 文件或环境变量中配置
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")  # 在 .env 文件或环境变量中配置
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
FREE_LIMIT = 5
AGENT_DEMO_MODE = os.getenv("AGENT_DEMO_MODE", "false").lower() == "true"

stripe.api_key = STRIPE_API_KEY

# FastAPI 应用初始化
app = FastAPI(title="Fast Video Download", description="通用视频下载 API 服务")

# 跨域配置：带凭证时不能使用通配符
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型：解析请求
class ParseRequest(BaseModel):
    url: str # 视频链接字符串

# 数据模型：下载请求
class DownloadRequest(BaseModel):
    url: str # 视频链接
    format_id: str = "best" # 目标格式 ID，默认为最佳画质
    is_audio_only: bool = False # 是否仅下载音频


class AgentRunRequest(BaseModel):
    message: str = ""
    session_id: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


class AgentChatRequest(BaseModel):
    message: str = ""
    session_id: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False


class AgentDownloadRequest(BaseModel):
    url: str
    format_id: str = "best"
    is_audio_only: bool = False
    session_id: Optional[str] = None

# 启动事件：确保数据库和下载目录存在并清理旧文件
@app.on_event("startup")
async def startup_event():
    # 初始化数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    # 清理一小时以上的临时视频文件，避免占用磁盘空间
    for filename in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                file_age = time.time() - os.path.getctime(file_path)
                if file_age > 3600:  # 超过 3600 秒
                    os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

# 接口 1: 健康检查
@app.get("/api/health")
async def health_check():
    return _build_health_response()


def _build_health_response() -> dict:
    ffmpeg_path = _find_ffmpeg_executable()
    ytdlp_available, ytdlp_detail = _check_ytdlp_available()

    return {
        "status": "ok",
        "backend": {
            "status": "running",
            "demo_mode": AGENT_DEMO_MODE,
            "python_version": sys.version.split()[0],
        },
        "demo_mode": AGENT_DEMO_MODE,
        "python_version": sys.version.split()[0],
        "download_directory": DOWNLOAD_DIR,
        "ffmpeg": {
            "available": bool(ffmpeg_path),
            "path": ffmpeg_path,
        },
        "yt_dlp": {
            "available": ytdlp_available,
            "detail": ytdlp_detail,
        },
    }


def _find_ffmpeg_executable() -> Optional[str]:
    direct_path = shutil.which("ffmpeg")
    if direct_path:
        return direct_path

    try:
        import static_ffmpeg

        paths = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
        return paths[0] if paths else None
    except Exception:
        return None


def _check_ytdlp_available() -> tuple[bool, str]:
    try:
        import yt_dlp

        version = getattr(yt_dlp.version, "__version__", "unknown")
        return True, version
    except Exception as exc:
        return False, str(exc)


@app.post("/api/agent/run")
async def run_agent_endpoint(request: AgentRunRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="缺少 message")

    return await _run_agent_request(
        request.message,
        request.session_id,
        request.context,
        dry_run=request.dry_run,
    )


@app.post("/api/agent/chat")
async def chat_agent_endpoint(request: AgentChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="缺少 message")

    if not _is_video_task_message(request.message, request.context):
        return {
            "status": "unsupported",
            "message": "当前仅支持视频相关任务",
        }

    if AGENT_DEMO_MODE:
        return _build_agent_demo_response(
            request.message,
            request.session_id,
            request.context,
            dry_run=request.dry_run,
        )

    response = await _run_agent_request(
        request.message,
        request.session_id,
        request.context,
        dry_run=request.dry_run,
        diagnostic=True,
    )
    if request.dry_run:
        return response
    return await _maybe_start_agent_download_from_message(response)


@app.post("/api/agent/download")
async def agent_download_endpoint(request: AgentDownloadRequest):
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="缺少 url")

    result = await _start_download_task(
        request.url,
        request.format_id,
        request.is_audio_only,
    )
    return {
        "task_id": result["task_id"],
        "status": result["status"],
        "selected_format": result["selected_format"],
        "progress": result["progress"],
    }


async def _run_agent_request(
    message: str,
    session_id: Optional[str],
    context: dict[str, Any],
    dry_run: bool = False,
    diagnostic: bool = False,
) -> dict:
    session_context = dict(context or {})
    if session_id:
        session_context["session_id"] = session_id

    try:
        if dry_run:
            result = await asyncio.to_thread(
                run_app_agent,
                message,
                session_context or None,
                dry_run=True,
            )
        else:
            result = await asyncio.to_thread(
                run_app_agent,
                message,
                session_context or None,
            )
        if diagnostic:
            return _build_real_agent_response(result, session_id, dry_run=dry_run)
        return _summarize_agent_result(result, session_id)
    except Exception as exc:
        if diagnostic:
            return _build_real_agent_exception_response(exc, session_id, dry_run=dry_run)
        raise


def _is_video_task_message(message: str, context: dict[str, Any]) -> bool:
    text = (message or "").lower()
    raw_text = message or ""
    if re.search(r"https?://[^\s]+", raw_text):
        return True
    if context and (context.get("url") or context.get("task_id")):
        return True

    keywords = (
        "video", "download", "audio", "mp3", "parse", "metadata",
        "status", "progress", "视频", "下载", "音频", "解析",
        "进度", "任务", "链接",
    )
    return any(keyword in text or keyword in raw_text for keyword in keywords)


def _summarize_agent_result(result: dict, session_id: Optional[str] = None) -> dict:
    execution = result.get("execution") or {}
    final_video = _extract_agent_video_result(execution)
    return {
        "status": result.get("status"),
        "session_id": session_id,
        "perception": result.get("perception"),
        "plan": result.get("plan"),
        "execution": {
            "ok": execution.get("ok"),
            "goal": execution.get("goal"),
            "error": execution.get("error"),
            "steps": [
                {
                    "ok": step.get("ok"),
                    "tool": step.get("tool"),
                    "error": step.get("error"),
                }
                for step in execution.get("steps", [])
            ],
        },
        "reflection": result.get("reflection"),
        "final_video": final_video,
        "suggested_next_action": _suggest_agent_next_action(result.get("status"), result.get("reflection")),
    }


def _build_real_agent_response(
    result: dict,
    session_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    perception = result.get("perception") or {}
    plan = result.get("plan") or {}
    execution = result.get("execution") or {}
    reflection = result.get("reflection") or {}
    final_result = _extract_agent_video_result(execution)
    ok = bool(execution.get("ok")) and reflection.get("status") == "ok"
    failed_step = _find_failed_agent_step(execution, plan)
    error = _agent_error_message(execution, reflection, failed_step)

    return {
        "status": result.get("status"),
        "mode": "real",
        "ok": ok,
        "session_id": session_id,
        "dry_run": dry_run or bool(result.get("dry_run")),
        "perception": perception,
        "plan": plan,
        "execution": execution,
        "reflection": reflection,
        "final_result": final_result,
        "final_video": final_result,
        "error": error,
        "debug": {
            "demo_mode": AGENT_DEMO_MODE,
            "selected_intent": perception.get("intent"),
            "selected_tools": _selected_tools(plan),
            "failed_step": failed_step,
            "exception_type": _exception_type_from_failed_step(failed_step),
            "exception_message": _exception_message_from_failed_step(failed_step, error),
            "raw_error_summary": _raw_error_summary(error),
        },
        "suggested_next_action": _suggest_agent_next_action(result.get("status"), reflection),
    }


def _build_real_agent_exception_response(
    exc: Exception,
    session_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    return {
        "status": "failed",
        "mode": "real",
        "ok": False,
        "session_id": session_id,
        "dry_run": dry_run,
        "perception": None,
        "plan": None,
        "execution": {
            "ok": False,
            "goal": None,
            "steps": [],
            "error": str(exc),
        },
        "reflection": {
            "status": "failed",
            "reason": str(exc),
            "repair_plan": [],
        },
        "final_result": None,
        "final_video": None,
        "error": str(exc),
        "debug": {
            "demo_mode": AGENT_DEMO_MODE,
            "selected_intent": None,
            "selected_tools": [],
            "failed_step": None,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "raw_error_summary": _raw_error_summary(str(exc)),
        },
        "suggested_next_action": "Agent 运行前发生异常，请检查后端日志和请求参数。",
    }


def _selected_tools(plan: dict) -> list[str]:
    return [
        step.get("tool")
        for step in plan.get("steps", [])
        if step.get("tool")
    ]


def _find_failed_agent_step(execution: dict, plan: dict) -> Optional[dict]:
    for index, step in enumerate(execution.get("steps", [])):
        if step.get("ok", False):
            continue

        plan_step = {}
        plan_steps = plan.get("steps") or []
        if index < len(plan_steps):
            plan_step = plan_steps[index] or {}

        return {
            "id": plan_step.get("id"),
            "tool": step.get("tool") or plan_step.get("tool"),
            "args": plan_step.get("args"),
            "error": step.get("error"),
            "exception_type": step.get("exception_type"),
            "exception_message": step.get("exception_message") or step.get("error"),
        }
    return None


def _agent_error_message(
    execution: dict,
    reflection: dict,
    failed_step: Optional[dict],
) -> Optional[str]:
    if failed_step:
        return failed_step.get("exception_message") or failed_step.get("error")
    if execution.get("error"):
        return execution.get("error")
    if reflection.get("status") not in (None, "ok"):
        return reflection.get("reason")
    return None


def _exception_type_from_failed_step(failed_step: Optional[dict]) -> Optional[str]:
    return failed_step.get("exception_type") if failed_step else None


def _exception_message_from_failed_step(
    failed_step: Optional[dict],
    error: Optional[str],
) -> Optional[str]:
    if failed_step:
        return failed_step.get("exception_message") or failed_step.get("error")
    return error


def _raw_error_summary(error: Optional[str]) -> Optional[str]:
    if not error:
        return None
    compact = " ".join(str(error).split())
    return compact[:500]


def _extract_agent_video_result(execution: dict) -> Optional[dict]:
    parsed_data = None
    download_data = None

    for step in execution.get("steps", []):
        data = step.get("data") or {}
        if step.get("tool") == "parse_video" and data:
            parsed_data = data
        if step.get("tool") == "download_video" and data:
            download_data = data

    if not parsed_data and not download_data:
        return None

    parsed_data = parsed_data or {}
    download_data = download_data or {}
    return {
        "title": parsed_data.get("title") or download_data.get("title"),
        "platform": parsed_data.get("platform"),
        "thumbnail": parsed_data.get("thumbnail"),
        "duration_string": parsed_data.get("duration_string"),
        "available_formats": parsed_data.get("formats", []),
        "audio_formats": parsed_data.get("audio_formats", []),
        "download_status": download_data.get("status"),
        "task_id": download_data.get("task_id"),
        "filepath": download_data.get("filepath"),
        "filename": download_data.get("filename"),
        "download_url": download_data.get("download_url"),
    }


async def _maybe_start_agent_download_from_message(response: dict) -> dict:
    final_result = response.get("final_result")
    if not final_result:
        return response

    plan = response.get("plan") or {}
    perception = response.get("perception") or {}
    intent = perception.get("intent")
    url = (perception.get("entities") or {}).get("url")
    if not url or intent not in ("download_video", "download_audio"):
        return response

    recommended_format = _select_recommended_format(final_result, plan, intent)
    if recommended_format:
        final_result["recommended_format"] = recommended_format
        response["final_video"] = final_result

    format_hint = plan.get("format_hint") or ((perception.get("constraints") or {}).get("format_hint"))
    if not _should_auto_start_download(format_hint):
        return response

    selected_format = _match_format_from_hint(final_result, format_hint, intent)
    if not selected_format:
        return response

    is_audio_only = bool(format_hint.get("is_audio_only")) or intent == "download_audio"
    task = await _start_download_task(
        url,
        selected_format.get("format_id", "best"),
        is_audio_only,
    )
    final_result.update({
        "download_status": task["status"],
        "task_id": task["task_id"],
        "filename": task.get("filename"),
        "download_url": task.get("download_url"),
        "selected_format": selected_format,
    })
    response["final_video"] = final_result
    response["agent_download"] = {
        "task_id": task["task_id"],
        "status": task["status"],
        "selected_format": selected_format,
        "progress": 0,
    }
    return response


def _select_recommended_format(
    final_result: dict,
    plan: dict,
    intent: Optional[str],
) -> Optional[dict]:
    format_hint = plan.get("format_hint") or {}
    matched = _match_format_from_hint(final_result, format_hint, intent)
    if matched:
        return matched

    if intent == "download_audio":
        audio_formats = final_result.get("audio_formats") or []
        return audio_formats[0] if audio_formats else None

    formats = final_result.get("available_formats") or []
    return formats[0] if formats else None


def _should_auto_start_download(format_hint: Optional[dict]) -> bool:
    if not format_hint:
        return False
    return bool(format_hint.get("format_id") or format_hint.get("resolution"))


def _match_format_from_hint(
    final_result: dict,
    format_hint: Optional[dict],
    intent: Optional[str],
) -> Optional[dict]:
    if not format_hint and intent != "download_audio":
        return None

    candidates = []
    if intent == "download_audio" or (format_hint or {}).get("is_audio_only"):
        candidates.extend(final_result.get("audio_formats") or [])
    candidates.extend(final_result.get("available_formats") or [])

    if not candidates:
        return None

    hint = format_hint or {}
    requested_format_id = hint.get("format_id")
    requested_resolution = hint.get("resolution")
    requested_ext = hint.get("ext")

    for candidate in candidates:
        if requested_format_id and str(candidate.get("format_id")) == str(requested_format_id):
            return candidate

    for candidate in candidates:
        if requested_resolution and int(candidate.get("height") or 0) != int(requested_resolution):
            continue
        if requested_ext and candidate.get("ext") != requested_ext:
            continue
        return candidate

    if intent == "download_audio":
        return candidates[0]
    return None


def _suggest_agent_next_action(status: Optional[str], reflection: Optional[dict]) -> str:
    if status == "planned":
        return "Dry-run 已完成：计划已生成，可以切换为真实执行来调用工具。"
    if status == "completed":
        return "解析完成：请选择一个格式，然后点击开始下载。"
    if reflection and reflection.get("status") == "needs_repair":
        return "建议根据 repair_plan 重新执行失败步骤。"
    return "请检查输入链接或稍后重试。"


def _build_agent_demo_response(
    message: str,
    session_id: Optional[str],
    context: dict[str, Any],
    dry_run: bool = False,
) -> dict:
    url = (context or {}).get("url") or "https://www.bilibili.com/video/BV1AgentDemo/"
    execution = {
        "ok": True,
        "goal": "download_video",
        "error": None,
        "steps": [],
        "dry_run": True,
    } if dry_run else {
        "ok": True,
        "goal": "download_video",
        "error": None,
        "steps": [
            {
                "ok": True,
                "tool": "parse_video",
                "error": None,
                "data": {
                    "title": "AI Agent 演示视频：从链接到任务计划",
                    "platform": "BiliBili",
                    "formats": [
                        {"format_id": "1080p", "label": "1080P · MP4", "height": 1080, "ext": "mp4"},
                        {"format_id": "720p", "label": "720P · MP4", "height": 720, "ext": "mp4"},
                        {"format_id": "audio", "label": "音频 · MP3", "height": 0, "ext": "mp3"},
                    ],
                },
            },
            {
                "ok": True,
                "tool": "download_video",
                "error": None,
                "data": {
                    "filename": "agent-demo-video.mp4",
                    "filepath": "/demo/agent-demo-video.mp4",
                    "title": "AI Agent 演示视频：从链接到任务计划",
                    "ext": "mp4",
                },
            },
        ],
    }
    final_result = {
        "title": "AI Agent 演示视频：从链接到任务计划",
        "platform": "BiliBili",
        "download_status": "completed",
        "task_id": "demo-task-id",
        "filename": "agent-demo-video.mp4",
        "download_url": "/api/download/fetch/demo-task-id",
        "available_formats": [
            {"format_id": "1080p", "label": "1080P · MP4", "height": 1080, "ext": "mp4"},
            {"format_id": "720p", "label": "720P · MP4", "height": 720, "ext": "mp4"},
            {"format_id": "audio", "label": "音频 · MP3", "height": 0, "ext": "mp3"},
        ],
    }
    return {
        "status": "planned" if dry_run else "completed",
        "mode": "demo",
        "ok": True,
        "session_id": session_id,
        "demo_mode": True,
        "dry_run": dry_run,
        "perception": {
            "intent": "download_video",
            "entities": {
                "url": url,
                "platform_hint": "bilibili",
            },
            "constraints": {
                "source": "demo_rule_based",
                "original_message": message,
            },
        },
        "plan": {
            "goal": "download_video",
            "steps": [
                {
                    "id": "s1",
                    "tool": "parse_video",
                    "args": {"url": url},
                },
                {
                    "id": "s2",
                    "tool": "download_video",
                    "args": {"url": url, "format_id": "best", "is_audio_only": False},
                },
            ],
        },
        "execution": execution,
        "reflection": {
            "status": "ok",
            "reason": "Dry-run 演示已完成：只生成计划，未模拟工具调用。" if dry_run else "演示模式下解析、计划、工具调用和结果检查均已完成。",
            "repair_plan": [],
        },
        "final_result": None if dry_run else final_result,
        "final_video": None if dry_run else final_result,
        "error": None,
        "debug": {
            "demo_mode": True,
            "selected_intent": "download_video",
            "selected_tools": ["parse_video", "download_video"],
            "failed_step": None,
            "exception_type": None,
            "exception_message": None,
            "raw_error_summary": None,
        },
        "suggested_next_action": "Dry-run 完成：确认计划后可以点击运行 Agent。" if dry_run else "展示完成：可以切换到真实模式，用实际视频链接执行同样的 Agent 流程。",
    }

# --- 用户与认证接口 ---

class UserCreate(BaseModel):
    email: str # 使用邮箱注册
    password: str

@app.post("/api/auth/register")
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.username == user_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")
    
    new_user = models.User(
        username=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_vip=False
    )
    db.add(new_user)
    await db.commit()
    return {"message": "注册成功"}

@app.post("/api/auth/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        form_data = await request.json()
    else:
        form_data = dict(await request.form())

    username = form_data.get("username")
    password = form_data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="缺少用户名或密码")
    
    result = await db.execute(select(models.User).filter(models.User.username == username))
    user = result.scalars().first()
    
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/user/me")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "is_vip": current_user.is_vip,
        "daily_download_count": current_user.daily_download_count,
        "role": "VIP" if current_user.is_vip else "FREE"
    }

# 接口：创建 Stripe 支付会话
@app.post("/api/stripe/create-checkout-session")
async def create_checkout_session(current_user: models.User = Depends(get_current_user)):
    try:
        if not STRIPE_API_KEY:
            raise HTTPException(status_code=503, detail="Stripe 尚未配置")

        # 创建一个一次性购买会话
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'alipay'], # 根据实际账号权限可选
            line_items=[
                {
                    'price_data': {
                        'currency': 'cny',
                        'product_data': {
                            'name': 'Fast Video Download VIP (1个月)',
                            'description': '解锁无限 AI 视频总结权限',
                        },
                        'unit_amount': 990, # 9.90 CNY
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f'{FRONTEND_BASE_URL}/?payment=success', # 支付成功回传
            cancel_url=f'{FRONTEND_BASE_URL}/?payment=cancel',
            metadata={
                "user_id": str(current_user.id)
            }
        )
        return {"url": checkout_session.url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 接口：Stripe Webhook 回调（重要：支付安全性核心）
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe Webhook 尚未配置")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print(f"Webhook 签名验证失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 处理支付成功事件
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # 彻底修复：将 StripeObject 转换为原生字典，确保 .get() 可用
        metadata = dict(getattr(session, 'metadata', {}))
        user_id = metadata.get("user_id")
        
        if user_id:
            # 找到对应用户并升级
            user_id = int(user_id)
            result = await db.execute(select(models.User).filter(models.User.id == user_id))
            user = result.scalars().first()
            if user:
                user.is_vip = True
                # 设置过期时间为当前时间的 30 天后
                if user.vip_expire_at and user.vip_expire_at > datetime.now():
                    user.vip_expire_at += timedelta(days=30)
                else:
                    user.vip_expire_at = datetime.now() + timedelta(days=30)
                
                await db.commit()
                print(f"用户 {user.username} 已通过 Stripe 升级为 VIP")

    return {"status": "success"}

# --- 视频功能逻辑 ---

# 接口 2: 视频解析
@app.post("/api/parse")
async def parse_video(request: ParseRequest, current_user: Optional[models.User] = Depends(get_current_user_optional)):
    try:
        raw_input = request.url.strip()
        if not raw_input:
            raise HTTPException(status_code=400, detail="请输入视频链接或搜索内容")
        # ... 原有解析逻辑 ...
        url = raw_input

        # 新增：@ 符号功能支持
        if raw_input.startswith("@"):
            # 模式 1: 平台快捷搜索 (例如 @yt amazing cats)
            shortcut_match = re.match(r"^@([a-z]+)\s+(.+)$", raw_input, re.IGNORECASE)
            if shortcut_match:
                platform_code = shortcut_match.group(1).lower()
                query = shortcut_match.group(2)
                
                # 映射平台代码到 yt-dlp 搜索前缀
                platform_map = {
                    "yt": "ytsearch5:",
                    "youtube": "ytsearch5:",
                    "bi": "bilibili:",
                    "bilibili": "bilibili:",
                    "tt": "tiktok:",
                    "tiktok": "tiktok:",
                }
                
                if platform_code in platform_map:
                    url = f"{platform_map[platform_code]}{query}"
            
            # 模式 2: 社交媒体 Handle (例如 @username)
            elif re.match(r"^@[a-zA-Z0-9._-]{3,30}$", raw_input):
                handle = raw_input[1:]
                # 默认解析为 YouTube Handle 链接
                url = f"https://www.youtube.com/@{handle}"
        
        # 原有逻辑：使用正则从可能的包含文字的消息中提取 URL
        if not url.startswith(("ytsearch", "bilibili:", "tiktok:")):
            match = re.search(r"https?://[^\s]+", url)
            url = match.group(0) if match else url
            if url.endswith('】'):
                url = url.rstrip('】')
        
        print(f"正在解析链接/查询: {url}")
        
        # 抖音链接特殊处理
        if "v.douyin.com" in url or "douyin.com" in url:
            if not url.startswith("http"):
                url = "https://" + url
            parser = DouyinParser()
            # 在单独线程中运行解析，避免阻塞异步主循环
            parsed_data = await asyncio.to_thread(parser.parse, url)
            if not parsed_data:
                 raise HTTPException(status_code=400, detail="抖音视频解析失败")
            return parsed_data
            
        # 通用平台使用 yt-dlp 解析（通过 VideoDownloader 中转）
        downloader = VideoDownloader()
        parsed_data = await asyncio.to_thread(downloader.parse_video, url)
        return parsed_data
    except HTTPException:
         raise
    except Exception as e:
         import traceback
         traceback.print_exc()
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/status/{task_id}")
async def get_task_status(task_id: str):
    """查询下载任务的实时进度"""
    status = task_status.get(task_id)
    if not status:
        return {"progress": 0, "status": "not_found"}
    return status


@app.get("/api/download/status/{task_id}")
async def get_download_status(task_id: str):
    """Agent/legacy compatible download task status endpoint."""
    return await get_task_status(task_id)


async def _start_download_task(
    url: str,
    format_id: str = "best",
    is_audio_only: bool = False,
) -> dict:
    if not url:
        raise HTTPException(status_code=400, detail="必须提供视频链接 URL")

    match = re.search(r"https?://[^\s]+", url)
    target_url = match.group(0) if match else url
    if target_url.endswith('】'):
        target_url = target_url.rstrip('】')

    task_id = create_download_task()

    def progress_callback(data):
        update_download_progress(task_id, data)

    async def run_download_task():
        try:
            if "douyin.com" in target_url:
                parser = DouyinParser()
                result = await asyncio.to_thread(
                    parser.download,
                    target_url,
                    "audio" if is_audio_only else "video",
                    progress_callback,
                )
            else:
                downloader = VideoDownloader()
                result = await asyncio.to_thread(
                    downloader.download_video,
                    target_url,
                    format_id,
                    is_audio_only,
                    progress_callback,
                )

            if result and os.path.exists(result["filepath"]):
                complete_download_task(
                    task_id,
                    result["filepath"],
                    os.path.basename(result["filepath"]),
                )
            else:
                fail_download_task(task_id, "下载失败，未生成文件")
        except Exception as e:
            print(f"任务 {task_id} 失败: {e}")
            fail_download_task(task_id, str(e))

    task_status[task_id]["status"] = "downloading"
    task_status[task_id]["message"] = "下载任务已启动"
    asyncio.create_task(run_download_task())

    return {
        "task_id": task_id,
        "status": task_status[task_id]["status"],
        "progress": task_status[task_id]["progress"],
        "selected_format": {
            "format_id": format_id,
            "is_audio_only": is_audio_only,
        },
    }

# 接口 3: 下载准备任务 (创建下载任务并后台执行)
@app.post("/api/download/prepare")
async def prepare_download(request: Request, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        body = await request.json()
        url = body.get("url")
        format_id = body.get("format_id", "best")
        is_audio_only = body.get("is_audio_only", False)

        if not url:
            raise HTTPException(status_code=400, detail="必须提供视频链接 URL")

        # 会员与配额检查
        today = str(date.today())
        if current_user.last_download_date != today:
            current_user.last_download_date = today
            current_user.daily_download_count = 0
        
        if not current_user.is_vip:
            if current_user.daily_download_count >= FREE_LIMIT:
                raise HTTPException(status_code=403, detail=f"每日限额已达 ({FREE_LIMIT}次)，请升级 VIP 享受无限下载")
        else:
            # VIP 检查：是否已过期
            if current_user.vip_expire_at and current_user.vip_expire_at < datetime.now():
                current_user.is_vip = False
                await db.commit()
                # 过期后退回普通用户限额检查
                if current_user.daily_download_count >= FREE_LIMIT:
                    raise HTTPException(status_code=403, detail="您的 VIP 已到期，且免费额度已用完，请续费")

        # 更新下载计数
        current_user.daily_download_count += 1
        await db.commit()

        # 预先清理 URL，处理带有标题的分享链接
        import re
        match = re.search(r"https?://[^\s]+", url)
        target_url = match.group(0) if match else url
        if target_url.endswith('】'): # 处理 B 站分享链接结尾多出的括号
             target_url = target_url.rstrip('】')

        result = await _start_download_task(target_url, format_id, is_audio_only)
        return {"task_id": result["task_id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 接口 4: 获取准备好的文件
@app.get("/api/download/fetch/{task_id}")
async def fetch_download(task_id: str):
    status = task_status.get(task_id)
    if not status or status["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务未完成或不存在")

    file_path = status["filepath"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已过期或丢失")

    filename = status["filename"]
    file_size = os.path.getsize(file_path)
    
    from urllib.parse import quote
    encoded_filename = quote(filename)

    async def file_streamer():
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    yield chunk
        finally:
            # 传输完成后清理，并移除任务追踪
            if os.path.exists(file_path):
                 try: os.unlink(file_path)
                 except: pass
            if task_id in task_status:
                 del task_status[task_id]

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        "Content-Length": str(file_size),
        "Content-Type": "application/octet-stream"
    }

    return StreamingResponse(file_streamer(), headers=headers)

# 接口 4: 封面图代理（绕过防盗链）
@app.get("/api/proxy/thumbnail")
async def proxy_thumbnail(url: str):
    """
    通过代理获取封面图，添加特定的 Referer 头部绕过 B站/YouTube 的防盗链保护
    """
    if not url:
        raise HTTPException(status_code=400, detail="缺乏 URL 参数")

    async def generate():
        try:
             async with httpx.AsyncClient() as client:
                  headers = {
                      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                  }
                  
                  # 根据链接域名设置伪造的 Referer
                  parsed = urlparse(url)
                  if "bilibili.com" in parsed.netloc or "hdslb.com" in parsed.netloc:
                      headers["Referer"] = "https://www.bilibili.com"
                  elif "youtube.com" in parsed.netloc or "ytimg.com" in parsed.netloc:
                      headers["Referer"] = "https://www.youtube.com"

                  async with client.stream("GET", url, headers=headers, follow_redirects=True, timeout=10.0) as response:
                      if response.status_code != 200:
                            yield b""
                            return
                      async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                            yield chunk
        except Exception as e:
             print(f"封面图代理失败: {url} - {e}")
             yield b""

    return StreamingResponse(generate(), media_type="image/jpeg")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
