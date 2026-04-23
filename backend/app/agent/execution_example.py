from app.agent.execution import execute_plan


def fake_tool_runner(name, **kwargs):
    return {
        "called_tool": name,
        "received_args": kwargs,
    }


def main():
    plan = {
        "goal": "download_video",
        "steps": [
            {
                "id": "s1",
                "tool": "parse_video",
                "args": {"url": "https://example.com/video"},
            },
            {
                "id": "s2",
                "tool": "download_video",
                "args": {
                    "url": "https://example.com/video",
                    "is_audio_only": False,
                },
            },
        ],
    }
    print(execute_plan(plan, tool_runner=fake_tool_runner))


if __name__ == "__main__":
    main()
