from tools.download import download_video
from tools.parse import parse_video


TOOLS = {
    "download_video": download_video,
    "parse_video": parse_video,
}


def get_tool(name: str):
    try:
        return TOOLS[name]
    except KeyError:
        raise ValueError(f"Unknown tool: {name}") from None
