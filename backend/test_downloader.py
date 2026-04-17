import asyncio
from downloader import VideoDownloader

async def test():
    dl = VideoDownloader()
    res = dl.download_video("https://www.bilibili.com/video/BV1sk4y1g7qS/?share_source=copy_web&vd_source=8e9d9e5ac20be4fa436ce3effb95b17d", "100047+bestaudio/best")
    print(res)

asyncio.run(test())
