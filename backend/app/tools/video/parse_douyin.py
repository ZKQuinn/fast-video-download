from douyin import DouyinParser


def parse_douyin(url: str) -> dict:
    """Parse Douyin video metadata by delegating to the existing Douyin parser."""
    if not url or not url.strip():
        raise ValueError("url is required")

    return DouyinParser().parse(url.strip())
