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
import time
import re
from typing import Optional
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, HTTPException, Request, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from downloader import VideoDownloader
from douyin import DouyinParser
import models
from database import engine, Base, get_db
from auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, datetime, timedelta
import stripe

# 常量与配置
DOWNLOAD_DIR = "downloads"
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")  # 在 .env 文件或环境变量中配置
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")  # 在 .env 文件或环境变量中配置

stripe.api_key = STRIPE_API_KEY

# 常量：下载临时文件存储目录
DOWNLOAD_DIR = "downloads"

# FastAPI 应用初始化
app = FastAPI(title="Fast Video Download", description="通用视频下载 API 服务")

# 跨域配置：允许前端所有源访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"status": "ok", "message": "服务运行正常"}

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
    # 支持 Form data 为 OAuth2 兼容，这里简化为从 JSON 获取
    form_data = await request.json()
    username = form_data.get("username")
    password = form_data.get("password")
    
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
            success_url='http://localhost:5173/?payment=success', # 支付成功回传
            cancel_url='http://localhost:5173/?payment=cancel',
            metadata={
                "user_id": current_user.id
            }
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 接口：Stripe Webhook 回调（重要：支付安全性核心）
@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
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
async def parse_video(request: ParseRequest, current_user: Optional[models.User] = Depends(get_current_user)):
    try:
        raw_input = request.url.strip()
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
    except Exception as e:
         import traceback
         traceback.print_exc()
         raise HTTPException(status_code=500, detail=str(e))

# 全局任务状态字典
# 格式: { task_id: { "progress": 0, "status": "preparing", "filename": "" } }
task_status = {}

@app.get("/api/task/status/{task_id}")
async def get_task_status(task_id: str):
    """查询下载任务的实时进度"""
    status = task_status.get(task_id)
    if not status:
        return {"progress": 0, "status": "not_found"}
    return status

# 接口 3: 执行下载并流化返回文件
# 支持 GET 和 POST。GET 用于浏览器原生下载显示进度，POST 保持兼容性。
# 全局变量：存储下载任务进度
download_tasks = {}

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
            FREE_LIMIT = 5 # 普通用户每天 5 次
            if current_user.daily_download_count >= FREE_LIMIT:
                raise HTTPException(status_code=403, detail=f"每日限额已达 ({FREE_LIMIT}次)，请升级 VIP 享受无限下载")
        else:
            # VIP 检查：是否已过期
            if current_user.vip_expire_at and current_user.vip_expire_at < datetime.now():
                current_user.is_vip = False
                await db.commit()
                # 过期后退回普通用户限额检查
                FREE_LIMIT = 5
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

        # 生成唯一的任务 ID
        import uuid
        task_id = str(uuid.uuid4())
        task_status[task_id] = {
            "progress": 0, 
            "status": "downloading", 
            "speed": "0 KB/s",
            "filename": "",
            "filepath": ""
        }

        # 定义进度回调
        def progress_callback(data):
            if task_id in task_status:
                task_status[task_id]["progress"] = data["progress_percent"]
                task_status[task_id]["download_type"] = data.get("download_type", "video")
                if data["status"] == "finished":
                    task_status[task_id]["status"] = "merging"
                else:
                    task_status[task_id]["status"] = "downloading"
                
                if data.get("speed"):
                    speed_mb = data["speed"] / (1024 * 1024)
                    task_status[task_id]["speed"] = f"{speed_mb:.1f} MB/s"

        # 在后台线程中启动下载
        async def run_download_task():
            try:
                # 抖音链接特殊路由：不走 yt-dlp
                if "douyin.com" in target_url:
                    parser = DouyinParser()
                    result = await asyncio.to_thread(
                        parser.download,
                        target_url,
                        "video",
                        progress_callback
                    )
                else:
                    # 通用平台
                    downloader = VideoDownloader()
                    result = await asyncio.to_thread(
                        downloader.download_video, 
                        target_url, 
                        format_id, 
                        is_audio_only, 
                        progress_callback
                    )
                
                if result and os.path.exists(result["filepath"]):
                    task_status[task_id]["status"] = "completed"
                    task_status[task_id]["filepath"] = result["filepath"]
                    task_status[task_id]["filename"] = os.path.basename(result["filepath"])
                    task_status[task_id]["progress"] = 100
                else:
                    task_status[task_id]["status"] = "failed"
            except Exception as e:
                print(f"任务 {task_id} 失败: {e}")
                task_status[task_id]["status"] = "failed"
                task_status[task_id]["error"] = str(e)

        # 启动后台任务
        asyncio.create_task(run_download_task())
        
        return {"task_id": task_id}

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
