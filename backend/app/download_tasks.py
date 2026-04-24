import os
import uuid
from typing import Any


task_status: dict[str, dict[str, Any]] = {}


def create_download_task() -> str:
    task_id = str(uuid.uuid4())
    task_status[task_id] = {
        "progress": 0,
        "status": "pending",
        "speed": "0 KB/s",
        "eta": None,
        "message": "任务已创建，等待下载",
        "error": None,
        "filename": "",
        "filepath": "",
    }
    return task_id


def update_download_progress(task_id: str, data: dict[str, Any]) -> None:
    if task_id not in task_status:
        return

    task = task_status[task_id]
    task["progress"] = data.get("progress_percent", task.get("progress", 0))
    task["download_type"] = data.get("download_type", task.get("download_type", "video"))
    task["status"] = "merging" if data.get("status") == "finished" else "downloading"
    task["message"] = "正在合并音视频" if task["status"] == "merging" else "正在下载"
    task["eta"] = data.get("eta", task.get("eta"))

    if data.get("speed"):
        speed_mb = data["speed"] / (1024 * 1024)
        task["speed"] = f"{speed_mb:.1f} MB/s"


def complete_download_task(
    task_id: str,
    filepath: str,
    filename: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    final_filename = filename or os.path.basename(filepath)
    task_status[task_id] = {
        **task_status.get(task_id, {}),
        "status": "completed",
        "filepath": filepath,
        "filename": final_filename,
        "progress": 100,
        "message": "下载完成",
        "error": None,
        "download_url": f"/api/download/fetch/{task_id}",
    }

    result = {
        "task_id": task_id,
        "filepath": filepath,
        "filename": final_filename,
        "download_url": f"/api/download/fetch/{task_id}",
        "status": "completed",
    }
    if extra:
        result.update(extra)
    return result


def fail_download_task(task_id: str, error: str) -> None:
    task_status[task_id] = {
        **task_status.get(task_id, {}),
        "status": "failed",
        "message": "下载失败",
        "error": error,
    }
