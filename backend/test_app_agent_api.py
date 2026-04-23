import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

import main


class AppAgentApiTests(unittest.TestCase):
    def test_agent_run_requires_message(self):
        client = TestClient(main.app)
        response = client.post("/api/agent/run", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "缺少 message")

    def test_agent_run_returns_summary(self):
        client = TestClient(main.app)
        fake_result = {
            "status": "completed",
            "perception": {
                "intent": "download_video",
                "entities": {"url": "https://example.com/video"},
                "constraints": {"source": "rule_based"},
            },
            "plan": {
                "goal": "download_video",
                "steps": [
                    {
                        "id": "s1",
                        "tool": "parse_video",
                        "args": {"url": "https://example.com/video"},
                    }
                ],
            },
            "execution": {
                "ok": True,
                "goal": "download_video",
                "steps": [
                    {
                        "ok": True,
                        "tool": "parse_video",
                        "data": {"large": "payload"},
                        "error": None,
                    }
                ],
                "error": None,
            },
            "reflection": {
                "status": "ok",
                "reason": "execution result satisfies the goal",
                "repair_plan": [],
            },
        }

        with patch.object(main, "run_app_agent", return_value=fake_result) as run_agent:
            response = client.post(
                "/api/agent/run",
                json={
                    "message": "帮我下载这个视频",
                    "session_id": "s-1",
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["session_id"], "s-1")
        self.assertEqual(body["perception"]["intent"], "download_video")
        self.assertEqual(body["plan"]["goal"], "download_video")
        self.assertEqual(
            body["execution"]["steps"],
            [{"ok": True, "tool": "parse_video", "error": None}],
        )
        self.assertEqual(body["reflection"]["status"], "ok")
        run_agent.assert_called_once_with(
            "帮我下载这个视频",
            {"url": "https://example.com/video", "session_id": "s-1"},
        )

    def test_agent_chat_returns_unsupported_for_plain_qa(self):
        client = TestClient(main.app)

        response = client.post(
            "/api/agent/chat",
            json={"message": "今天天气怎么样"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "unsupported",
            "message": "当前仅支持视频相关任务",
        })

    def test_agent_chat_routes_video_task_to_orchestrator(self):
        client = TestClient(main.app)
        fake_result = {
            "status": "completed",
            "perception": {
                "intent": "download_video",
                "entities": {"url": "https://example.com/video"},
                "constraints": {"source": "rule_based"},
            },
            "plan": {
                "goal": "download_video",
                "steps": [],
            },
            "execution": {
                "ok": True,
                "goal": "download_video",
                "steps": [],
                "error": None,
            },
            "reflection": {
                "status": "ok",
                "reason": "execution result satisfies the goal",
                "repair_plan": [],
            },
        }

        with patch.object(main, "run_app_agent", return_value=fake_result) as run_agent:
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我下载这个视频",
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "completed")
        self.assertEqual(response.json()["perception"]["intent"], "download_video")
        run_agent.assert_called_once_with(
            "帮我下载这个视频",
            {"url": "https://example.com/video"},
        )


if __name__ == "__main__":
    unittest.main()
