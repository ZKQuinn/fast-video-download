from tools.registry import get_tool


def execute_plan(plan: dict, context: dict) -> dict:
    """Execute the selected tool and normalize the result."""
    tool_name = plan.get("tool")
    tool = get_tool(tool_name)

    try:
        if tool_name == "download_video":
            data = tool(
                context["url"],
                format_id=plan.get("format_id", "best"),
                is_audio_only=plan.get("is_audio_only", False),
            )
        elif tool_name == "parse_video":
            data = tool(context["url"])
        else:
            raise ValueError(f"Unsupported tool: {tool_name}")

        return {
            "ok": True,
            "tool": tool_name,
            "data": data,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "data": None,
            "error": str(exc),
        }
