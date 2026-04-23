from app.tools.base import Tool
from app.tools.video.download_video import download_video
from app.tools.video.parse_douyin import parse_douyin
from app.tools.video.parse_video import parse_video


URL_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "Video URL or share text containing a video URL.",
        },
    },
    "required": ["url"],
}

DOWNLOAD_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "Video URL or share text containing a video URL.",
        },
        "format_id": {
            "type": "string",
            "description": "yt-dlp format id, defaults to best.",
            "default": "best",
        },
        "is_audio_only": {
            "type": "boolean",
            "description": "Download audio only when true.",
            "default": False,
        },
    },
    "required": ["url"],
}

TOOLS: dict[str, Tool] = {
    "parse_video": Tool(
        name="parse_video",
        description="Parse video metadata and available download formats from a URL.",
        input_schema=URL_SCHEMA,
        handler=parse_video,
    ),
    "download_video": Tool(
        name="download_video",
        description="Download a video or audio file from a URL.",
        input_schema=DOWNLOAD_SCHEMA,
        handler=download_video,
    ),
    "parse_douyin": Tool(
        name="parse_douyin",
        description="Parse Douyin video metadata from a Douyin URL.",
        input_schema=URL_SCHEMA,
        handler=parse_douyin,
    ),
}


def get_tool(name: str) -> Tool:
    try:
        return TOOLS[name]
    except KeyError:
        raise ValueError(f"Unknown tool: {name}") from None


def run_tool(name: str, **kwargs) -> dict:
    return get_tool(name).run(**kwargs)


def list_tools() -> list[dict]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }
        for tool in TOOLS.values()
    ]
