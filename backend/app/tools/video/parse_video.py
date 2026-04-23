from douyin import DouyinParser, is_douyin_url
from downloader import VideoDownloader


def parse_video(url: str) -> dict:
    """Parse video metadata by delegating to the existing parser logic."""
    if not url or not url.strip():
        raise ValueError("url is required")

    target_url = url.strip()
    if is_douyin_url(target_url):
        return DouyinParser().parse(target_url)

    return VideoDownloader().parse_video(target_url)
