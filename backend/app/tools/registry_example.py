from app.tools.registry import list_tools, run_tool


def main():
    print("Registered tools:")
    for tool in list_tools():
        print(f"- {tool['name']}: {tool['description']}")

    # Example call shape. Replace with a real URL to execute parsing.
    # result = run_tool("parse_video", url="https://www.example.com/video")
    # print(result)


if __name__ == "__main__":
    main()
