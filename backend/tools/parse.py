from downloader import VideoDownloader


def parse_video(url: str) -> dict:
    """Parse video metadata by delegating to the existing downloader implementation."""
    downloader = VideoDownloader()
    return downloader.parse_video(url)
