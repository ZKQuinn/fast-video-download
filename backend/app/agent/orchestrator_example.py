from app.agent.orchestrator import run


def fake_tool_runner(name, **kwargs):
    if name == "parse_video":
        return {"title": "demo video", "formats": [{"format_id": "best"}]}
    if name == "download_video":
        return {"filepath": __file__, "filename": "demo.mp4"}
    raise ValueError(f"unknown tool: {name}")


def main():
    result = run(
        "帮我下载这个视频 https://example.com/video",
        tool_runner=fake_tool_runner,
    )
    print(result)


if __name__ == "__main__":
    main()
