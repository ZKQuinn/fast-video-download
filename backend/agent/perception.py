def perceive(url: str) -> dict:
    """Convert raw user input into the minimal agent context."""
    normalized_url = (url or "").strip()
    return {
        "url": normalized_url,
        "intent": "download_video",
    }
