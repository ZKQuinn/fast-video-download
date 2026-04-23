from douyin import DouyinParser, is_douyin_url
from downloader import VideoDownloader


def download_video(
    url: str,
    format_id: str = "best",
    is_audio_only: bool = False,
    progress_callback=None,
) -> dict:
    """Download media by delegating to the existing downloader logic."""
    if not url or not url.strip():
        raise ValueError("url is required")

    target_url = url.strip()
    if is_douyin_url(target_url):
        mode = "audio" if is_audio_only else "video"
        return DouyinParser().download(target_url, mode, progress_callback)

    return VideoDownloader().download_video(
        target_url,
        format_id,
        is_audio_only,
        progress_callback,
    )
