from downloader import VideoDownloader


def download_video(url: str, format_id: str = "best", is_audio_only: bool = False) -> dict:
    """Download a video by delegating to the existing downloader implementation."""
    downloader = VideoDownloader()
    return downloader.download_video(
        url=url,
        format_id=format_id,
        is_audio_only=is_audio_only,
    )
