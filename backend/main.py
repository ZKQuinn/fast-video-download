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

# Constants
DOWNLOAD_DIR = "downloads"

# App initialization
app = FastAPI(title="Fast Video Download", description="API for universal video downloading")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ParseRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: str = "best"
    is_audio_only: bool = False

# Lifespan context manager for cleanup
@app.on_event("startup")
async def startup_event():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    for filename in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path):
                file_age = time.time() - os.path.getctime(file_path)
                if file_age > 3600:  # Clean files older than 1 hour
                    os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

# API Endpoints
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}

@app.post("/api/parse")
async def parse_video(request: ParseRequest):
    try:
        # Extract url from potentially noisy text using regex
        match = re.search(r"https?://[^\s]+", request.url)
        url = match.group(0) if match else request.url
        print(f"Parsing URL: {url}")
        
        # Specific handling for Douyin
        if url.startswith("v.douyin.com") or "douyin.com" in url:
            if not url.startswith("http"):
                url = "https://" + url
            parsed_data = await DouyinParser.parse(url)
            if not parsed_data:
                 raise HTTPException(status_code=400, detail="Failed to parse Douyin video")
            return parsed_data
            
        # General handling with yt-dlp
        downloader = VideoDownloader()
        parsed_data = await asyncio.to_thread(downloader.parse_video, url)
        return parsed_data
    except Exception as e:
         import traceback
         traceback.print_exc()
         raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download")
async def download_video(request: DownloadRequest):
    try:
        # Extract url from potentially noisy text using regex
        match = re.search(r"https?://[^\s]+", request.url)
        url = match.group(0) if match else request.url
        
        format_id = request.format_id
        is_audio = request.is_audio_only
        print(f"Downloading: {url}, Format: {format_id}, Audio: {is_audio}")

        # Try mapping douyin url
        if "douyin.com" in url or "v.douyin.com" in url:
             if not url.startswith("http"):
                url = "https://" + url
             parsed_data = await DouyinParser.parse(url)
             if parsed_data and parsed_data.get('formats'):
                 for fmt in parsed_data['formats']:
                     if fmt['format_id'] == format_id:
                         url = fmt['url']
                         break
             
        downloader = VideoDownloader()
        result = await asyncio.to_thread(
            downloader.download_video,
            url,
            format_id
        )

        if not result or not os.path.exists(result["filepath"]):
             raise HTTPException(status_code=500, detail="Download failed or file not found")

        file_path = result["filepath"]
        
        # Function to stream and delete file after download
        async def file_streamer():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192 * 1024):  # 8MB chunks
                        yield chunk
            finally:
                if os.path.exists(file_path):
                     try:
                         os.unlink(file_path)
                     except Exception as e:
                         print(f"Error removing temp file {file_path}: {e}")

        filename = os.path.basename(file_path)
        # URL-encode filename for Content-Disposition (supports Unicode/Chinese chars)
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

@app.get("/api/proxy/thumbnail")
async def proxy_thumbnail(url: str):
    """
    Proxy thumbnail images to bypass hotlinking protection (Referer checks)
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")

    async def generate():
        try:
             async with httpx.AsyncClient() as client:
                  headers = {
                      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                  }
                  
                  # Set referer depending on domain
                  parsed = urlparse(url)
                  if "bilibili.com" in parsed.netloc or "hdslb.com" in parsed.netloc:
                      headers["Referer"] = "https://www.bilibili.com"
                  elif "youtube.com" in parsed.netloc or "ytimg.com" in parsed.netloc:
                      headers["Referer"] = "https://www.youtube.com"

                  async with client.stream("GET", url, headers=headers, follow_redirects=True, timeout=10.0) as response:
                      if response.status_code != 200:
                           # Yield a 1x1 empty pixel or just let it fail
                           yield b""
                           return
                      async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                           yield chunk
        except Exception as e:
             print(f"Thumbnail proxy failed: {url} - {e}")
             yield b""

    return StreamingResponse(generate(), media_type="image/jpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
