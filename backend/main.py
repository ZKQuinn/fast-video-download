import asyncio
import os
import time
import re
from urllib.parse import urlparse
import httpx
from fastapi import FastAPI, HTTPException, Request
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
@app.post("/api/download")
async def download_video(request: DownloadRequest):
    try:
        # 提取 URL
        match = re.search(r"https?://[^\s]+", request.url)
        url = match.group(0) if match else request.url
        
        format_id = request.format_id
        is_audio = request.is_audio_only
        print(f"正在下载: {url}, 格式: {format_id}, 模式: {'仅音频' if is_audio else '视频'}")

        # 抖音下载（使用内部逻辑）
        if "douyin.com" in url or "v.douyin.com" in url:
             if not url.startswith("http"):
                url = "https://" + url
             parser = DouyinParser()
             mode = "audio" if is_audio else "video"
             result = await asyncio.to_thread(parser.download, url, mode)
        else:
             # 其他平台使用 yt-dlp+FFmpeg 实现合并下载
             downloader = VideoDownloader()
             result = await asyncio.to_thread(
                 downloader.download_video,
                 url,
                 format_id,
                 is_audio_only=is_audio
             )

        if not result or not os.path.exists(result["filepath"]):
             raise HTTPException(status_code=500, detail="文件下载失败或路径不存在")

        file_path = result["filepath"]
        
        # 生成器函数：通过流式响应读取文件，并在发送完毕后自动删除临时文件
        async def file_streamer():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192 * 1024):  # 每次读取 8MB
                        yield chunk
            finally:
                if os.path.exists(file_path):
                     try:
                         os.unlink(file_path) # 删除服务器临时文件
                         print(f"临时文件已清理: {file_path}")
                     except Exception as e:
                         print(f"清理临时文件失败 {file_path}: {e}")

        filename = os.path.basename(file_path)
        # 对中文文件名进行 URL 编码，确保浏览器下载对话框正常显示中文
        from urllib.parse import quote
        encoded_filename = quote(filename)
        headers = {
             "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
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
