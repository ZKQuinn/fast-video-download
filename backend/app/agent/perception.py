import re
from typing import Any


SUPPORTED_INTENTS = {
    "download_video",
    "download_audio",
    "parse_video",
    "get_task_status",
}

URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)
TASK_ID_PATTERN = re.compile(
    r"(?:task[_\s-]?id|任务|进度|status)[:：\s#-]*([a-f0-9-]{8,})",
    re.IGNORECASE,
)


def perceive(
    user_request: str,
    url: str | None = None,
    session_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert a user request into a minimal structured task context."""
    text = (user_request or "").strip()
    context = session_context or {}
    extracted_url = _normalize_url(url) or _extract_url(text) or context.get("url")
    intent = _detect_intent(text)

    entities: dict[str, Any] = {}
    if extracted_url:
        entities["url"] = extracted_url

    task_id = _extract_task_id(text) or context.get("task_id")
    if intent == "get_task_status" and task_id:
        entities["task_id"] = task_id

    constraints = {
        "source": "rule_based",
    }
    if context:
        constraints["session_context"] = context
    if intent == "download_audio":
        constraints["is_audio_only"] = True

    return {
        "intent": intent,
        "entities": entities,
        "constraints": constraints,
    }


def _detect_intent(text: str) -> str:
    lowered = text.lower()

    if any(keyword in lowered for keyword in ("task status", "status", "progress")):
        return "get_task_status"
    if any(keyword in text for keyword in ("任务状态", "查询任务", "下载进度", "进度")):
        return "get_task_status"
    if any(keyword in lowered for keyword in ("audio", "mp3", "music")):
        return "download_audio"
    if any(keyword in text for keyword in ("音频", "音乐", "提取声音", "mp3")):
        return "download_audio"
    if any(keyword in lowered for keyword in ("parse", "metadata", "info")):
        return "parse_video"
    if any(keyword in text for keyword in ("解析", "信息", "元数据")):
        return "parse_video"

    return "download_video"


def _extract_url(text: str) -> str | None:
    match = URL_PATTERN.search(text or "")
    if not match:
        return None
    return _normalize_url(match.group(0))


def _normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().strip('"').strip("'").rstrip(").,;!?】")


def _extract_task_id(text: str) -> str | None:
    match = TASK_ID_PATTERN.search(text or "")
    if not match:
        return None
    return match.group(1)
