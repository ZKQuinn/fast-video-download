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
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from downloader import VideoDownloader
from douyin import DouyinParser

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

# 启动事件：确保下载目录存在并清理旧文件
@app.on_event("startup")
async def startup_event():
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

# 接口 2: 视频解析
@app.post("/api/parse")
async def parse_video(request: ParseRequest):
    try:
        # 使用正则从可能的包含文字的消息中提取 URL
        match = re.search(r"https?://[^\s]+", request.url)
        url = match.group(0) if match else request.url
        print(f"正在解析链接: {url}")
        
        # 抖音链接特殊处理
        if url.startswith("v.douyin.com") or "douyin.com" in url:
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

# 接口 3: 执行下载并流化返回文件
# 支持 GET 和 POST。GET 用于浏览器原生下载显示进度，POST 保持兼容性。
@app.api_route("/api/download", methods=["GET", "POST"])
async def download_video(
    request: Request,
    url: Optional[str] = Query(None),
    format_id: Optional[str] = Query("best"),
    is_audio_only: Optional[bool] = Query(False)
):
    try:
        # 如果是 POST 请求，尝试从 JSON Body 中读取参数
        if request.method == "POST":
            try:
                body = await request.json()
                if not url: url = body.get("url")
                if format_id == "best": format_id = body.get("format_id", "best")
                if not is_audio_only: is_audio_only = body.get("is_audio_only", False)
            except:
                pass

        if not url:
            raise HTTPException(status_code=400, detail="必须提供视频链接 URL")

        # 提取 URL
        match = re.search(r"https?://[^\s]+", url)
        target_url = match.group(0) if match else url
        print(f"执行下载任务: {target_url}, 格式: {format_id}, 模式: {'仅音频' if is_audio_only else '视频'}")

        # 1. 执行下载任务
        if "douyin.com" in target_url or "v.douyin.com" in target_url:
             if not target_url.startswith("http"):
                target_url = "https://" + target_url
             parser = DouyinParser()
             mode = "audio" if is_audio_only else "video"
             result = await asyncio.to_thread(parser.download, target_url, mode)
        else:
             downloader = VideoDownloader()
             result = await asyncio.to_thread(
                 downloader.download_video,
                 target_url,
                 format_id,
                 is_audio_only=is_audio_only
             )

        if not result or not os.path.exists(result["filepath"]):
             raise HTTPException(status_code=500, detail="本地下载任务失败")

        file_path = result["filepath"]
        file_size = os.path.getsize(file_path) # 获取文件大小以支持浏览器进度显示
        filename = os.path.basename(file_path)
        
        # 编码文件名以支持中文
        from urllib.parse import quote
        encoded_filename = quote(filename)

        # 2. 准备流式响应
        async def file_streamer():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(1024 * 1024):  # 1MB 采样块
                        yield chunk
            finally:
                # 传输完成后删除临时文件
                if os.path.exists(file_path):
                      try:
                          os.unlink(file_path)
                          print(f"清理临时下载文件: {file_path}")
                      except:
                          pass

        # 设置关键响应头：
        # Content-Disposition: 触发下载对话框（仅使用 UTF-8 编码版本以避免 latin-1 错误）
        # Content-Length: 让浏览器显示进度百分比和剩余时间
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(file_size)
        }

        return StreamingResponse(
            file_streamer(), 
            media_type="application/octet-stream",
            headers=headers
        )

    except Exception as e:
        print(f"Download processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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
