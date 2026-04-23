import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app.agent.perception import perceive


class AppPerceptionTests(unittest.TestCase):
    def test_detects_download_video_with_url(self):
        self.assertEqual(
            perceive("帮我下载这个视频 https://example.com/watch?v=1"),
            {
                "intent": "download_video",
                "entities": {"url": "https://example.com/watch?v=1"},
                "constraints": {"source": "rule_based"},
            },
        )

    def test_detects_download_audio_with_explicit_url(self):
        self.assertEqual(
            perceive(
                "提取音频",
                url="https://example.com/video",
                session_context={"user_id": 7},
            ),
            {
                "intent": "download_audio",
                "entities": {"url": "https://example.com/video"},
                "constraints": {
                    "source": "rule_based",
                    "session_context": {"user_id": 7},
                    "is_audio_only": True,
                },
            },
        )

    def test_detects_parse_video(self):
        self.assertEqual(
            perceive("解析一下 https://example.com/video 的信息"),
            {
                "intent": "parse_video",
                "entities": {"url": "https://example.com/video"},
                "constraints": {"source": "rule_based"},
            },
        )

    def test_detects_task_status_with_context_task_id(self):
        self.assertEqual(
            perceive("查一下下载进度", session_context={"task_id": "abc12345"}),
            {
                "intent": "get_task_status",
                "entities": {"task_id": "abc12345"},
                "constraints": {
                    "source": "rule_based",
                    "session_context": {"task_id": "abc12345"},
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
