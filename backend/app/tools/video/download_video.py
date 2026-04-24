import os

from app.download_tasks import (
    complete_download_task,
    create_download_task,
    fail_download_task,
    update_download_progress,
)
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
    task_id = create_download_task()

    def agent_progress_callback(data):
        update_download_progress(task_id, data)
        if progress_callback:
            progress_callback(data)

    try:
        if is_douyin_url(target_url):
            mode = "audio" if is_audio_only else "video"
            result = DouyinParser().download(target_url, mode, agent_progress_callback)
        else:
            result = VideoDownloader().download_video(
                target_url,
                format_id,
                is_audio_only,
                agent_progress_callback,
            )

        filepath = (result or {}).get("filepath")
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"downloaded file does not exist: {filepath}")

        filename = (result or {}).get("filename") or os.path.basename(filepath)
        return complete_download_task(
            task_id,
            filepath,
            filename,
            {
                "title": (result or {}).get("title"),
                "ext": (result or {}).get("ext"),
            },
        )
    except Exception as exc:
        fail_download_task(task_id, str(exc))
        raise
