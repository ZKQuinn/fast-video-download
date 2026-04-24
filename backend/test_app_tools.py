import os
import sys
import unittest
from unittest.mock import ANY, patch

sys.path.insert(0, os.path.dirname(__file__))

from app.tools.registry import get_tool, list_tools, run_tool
from app.download_tasks import task_status


class AppToolsTests(unittest.TestCase):
    def test_registry_returns_video_tools(self):
        self.assertEqual(get_tool("parse_video").name, "parse_video")
        self.assertEqual(get_tool("download_video").name, "download_video")
        self.assertEqual(get_tool("parse_douyin").name, "parse_douyin")

    def test_registry_exposes_input_schema(self):
        tool = get_tool("download_video")

        self.assertIn("url", tool.input_schema["properties"])
        self.assertIn("format_id", tool.input_schema["properties"])
        self.assertIn("is_audio_only", tool.input_schema["properties"])
        self.assertEqual(tool.input_schema["required"], ["url"])

    def test_list_tools_returns_metadata(self):
        tool_names = {tool["name"] for tool in list_tools()}

        self.assertEqual(
            tool_names,
            {"parse_video", "download_video", "parse_douyin"},
        )

    def test_parse_video_delegates_to_existing_downloader(self):
        with patch("app.tools.video.parse_video.VideoDownloader") as downloader_cls:
            downloader_cls.return_value.parse_video.return_value = {"title": "demo"}

            result = run_tool("parse_video", url="https://example.com/video")

        self.assertEqual(result, {"title": "demo"})
        downloader_cls.return_value.parse_video.assert_called_once_with(
            "https://example.com/video"
        )

    def test_download_video_delegates_to_existing_downloader(self):
        task_status.clear()
        with patch("app.tools.video.download_video.VideoDownloader") as downloader_cls, patch(
            "app.tools.video.download_video.os.path.exists",
            return_value=True,
        ):
            downloader_cls.return_value.download_video.return_value = {
                "filepath": "/tmp/demo.mp4",
                "filename": "demo.mp4",
                "title": "demo",
                "ext": "mp4",
            }

            result = run_tool(
                "download_video",
                url="https://example.com/video",
                format_id="best",
                is_audio_only=False,
            )

        self.assertEqual(result["filepath"], "/tmp/demo.mp4")
        self.assertEqual(result["filename"], "demo.mp4")
        self.assertEqual(result["status"], "completed")
        self.assertIn("/api/download/fetch/", result["download_url"])
        self.assertIn(result["task_id"], task_status)
        downloader_cls.return_value.download_video.assert_called_once_with(
            "https://example.com/video",
            "best",
            False,
            ANY,
        )

    def test_download_video_failure_keeps_failed_task_status(self):
        task_status.clear()
        with patch("app.tools.video.download_video.VideoDownloader") as downloader_cls:
            downloader_cls.return_value.download_video.side_effect = RuntimeError("yt-dlp failed")

            with self.assertRaises(RuntimeError):
                run_tool(
                    "download_video",
                    url="https://example.com/video",
                    format_id="best",
                    is_audio_only=False,
                )

        self.assertEqual(len(task_status), 1)
        failed_task = next(iter(task_status.values()))
        self.assertEqual(failed_task["status"], "failed")
        self.assertIn("yt-dlp failed", failed_task["error"])

    def test_parse_douyin_delegates_to_existing_douyin_parser(self):
        with patch("app.tools.video.parse_douyin.DouyinParser") as parser_cls:
            parser_cls.return_value.parse.return_value = {"title": "douyin demo"}

            result = run_tool("parse_douyin", url="https://v.douyin.com/demo/")

        self.assertEqual(result, {"title": "douyin demo"})
        parser_cls.return_value.parse.assert_called_once_with(
            "https://v.douyin.com/demo/"
        )

    def test_tool_rejects_empty_url(self):
        with self.assertRaises(ValueError):
            run_tool("parse_video", url="")


if __name__ == "__main__":
    unittest.main()
