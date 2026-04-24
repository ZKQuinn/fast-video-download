import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

import main
from app.download_tasks import task_status


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

        with patch.object(main, "AGENT_DEMO_MODE", False), patch.object(
            main,
            "run_app_agent",
            return_value=fake_result,
        ) as run_agent:
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我下载这个视频",
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["mode"], "real")
        self.assertTrue(body["ok"])
        self.assertEqual(body["perception"]["intent"], "download_video")
        self.assertEqual(body["debug"]["selected_tools"], [])
        run_agent.assert_called_once_with(
            "帮我下载这个视频",
            {"url": "https://example.com/video"},
        )

    def test_agent_chat_dry_run_returns_plan_without_execution(self):
        client = TestClient(main.app)
        fake_result = {
            "status": "planned",
            "dry_run": True,
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
                "steps": [],
                "error": None,
                "dry_run": True,
            },
            "reflection": {
                "status": "ok",
                "reason": "dry_run enabled; execution skipped after planning",
                "repair_plan": [],
            },
        }

        with patch.object(main, "AGENT_DEMO_MODE", False), patch.object(
            main,
            "run_app_agent",
            return_value=fake_result,
        ) as run_agent:
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我下载这个视频",
                    "dry_run": True,
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "planned")
        self.assertTrue(body["dry_run"])
        self.assertEqual(body["execution"]["steps"], [])
        self.assertEqual(body["debug"]["selected_tools"], ["parse_video"])
        run_agent.assert_called_once_with(
            "帮我下载这个视频",
            {"url": "https://example.com/video"},
            dry_run=True,
        )

    def test_agent_chat_real_failure_includes_debug(self):
        client = TestClient(main.app)
        fake_result = {
            "status": "needs_repair",
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
                "ok": False,
                "goal": "download_video",
                "steps": [
                    {
                        "ok": False,
                        "tool": "parse_video",
                        "data": None,
                        "error": "HTTP Error 412: Precondition Failed",
                        "exception_type": "HTTPError",
                        "exception_message": "HTTP Error 412: Precondition Failed",
                    }
                ],
                "error": "HTTP Error 412: Precondition Failed",
            },
            "reflection": {
                "status": "needs_repair",
                "reason": "HTTP Error 412: Precondition Failed",
                "repair_plan": [],
            },
        }

        with patch.object(main, "AGENT_DEMO_MODE", False), patch.object(
            main,
            "run_app_agent",
            return_value=fake_result,
        ):
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我下载这个视频",
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertEqual(body["debug"]["failed_step"]["id"], "s1")
        self.assertEqual(body["debug"]["exception_type"], "HTTPError")
        self.assertIn("412", body["error"])
        self.assertIn("412", body["debug"]["raw_error_summary"])

    def test_agent_chat_real_success_returns_download_url(self):
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
                    {"id": "s1", "tool": "parse_video", "args": {"url": "https://example.com/video"}},
                    {"id": "s2", "tool": "download_video", "args": {"url": "https://example.com/video"}},
                ],
            },
            "execution": {
                "ok": True,
                "goal": "download_video",
                "steps": [
                    {
                        "ok": True,
                        "tool": "parse_video",
                        "data": {
                            "title": "demo video",
                            "platform": "Example",
                            "formats": [{"format_id": "best", "label": "Best"}],
                        },
                        "error": None,
                    },
                    {
                        "ok": True,
                        "tool": "download_video",
                        "data": {
                            "task_id": "task-1",
                            "filepath": "/tmp/demo.mp4",
                            "filename": "demo.mp4",
                            "download_url": "/api/download/fetch/task-1",
                            "status": "completed",
                        },
                        "error": None,
                    },
                ],
                "error": None,
            },
            "reflection": {
                "status": "ok",
                "reason": "execution result satisfies the goal",
                "repair_plan": [],
            },
        }

        with patch.object(main, "AGENT_DEMO_MODE", False), patch.object(
            main,
            "run_app_agent",
            return_value=fake_result,
        ):
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我下载这个视频",
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["final_result"]["title"], "demo video")
        self.assertEqual(body["final_result"]["download_status"], "completed")
        self.assertEqual(body["final_result"]["filename"], "demo.mp4")
        self.assertEqual(body["final_result"]["download_url"], "/api/download/fetch/task-1")

    def test_agent_chat_parse_only_does_not_create_download_task(self):
        client = TestClient(main.app)
        task_status.clear()
        fake_result = {
            "status": "completed",
            "perception": {
                "intent": "parse_video",
                "entities": {"url": "https://example.com/video"},
                "constraints": {"source": "rule_based"},
            },
            "plan": {
                "goal": "parse_video",
                "steps": [
                    {"id": "s1", "tool": "parse_video", "args": {"url": "https://example.com/video"}},
                ],
            },
            "execution": {
                "ok": True,
                "goal": "parse_video",
                "steps": [
                    {
                        "ok": True,
                        "tool": "parse_video",
                        "data": {
                            "title": "demo video",
                            "platform": "Example",
                            "formats": [{"format_id": "best", "label": "Best"}],
                        },
                        "error": None,
                    },
                ],
                "error": None,
            },
            "reflection": {
                "status": "ok",
                "reason": "execution result satisfies the goal",
                "repair_plan": [],
            },
        }

        with patch.object(main, "AGENT_DEMO_MODE", False), patch.object(
            main,
            "run_app_agent",
            return_value=fake_result,
        ):
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我解析这个视频",
                    "context": {"url": "https://example.com/video"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["plan"]["steps"][0]["tool"], "parse_video")
        self.assertIsNone(body["final_result"]["download_status"])
        self.assertEqual(task_status, {})

    def test_agent_download_creates_task_id(self):
        client = TestClient(main.app)
        starter = AsyncMock(return_value={
            "task_id": "task-1",
            "status": "downloading",
            "progress": 0,
            "selected_format": {"format_id": "22", "is_audio_only": False},
        })

        with patch.object(main, "_start_download_task", starter):
            response = client.post(
                "/api/agent/download",
                json={
                    "url": "https://example.com/video",
                    "format_id": "22",
                    "is_audio_only": False,
                    "session_id": "s1",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["task_id"], "task-1")
        self.assertEqual(body["selected_format"]["format_id"], "22")
        starter.assert_awaited_once_with("https://example.com/video", "22", False)

    def test_download_status_completed_returns_download_url(self):
        client = TestClient(main.app)
        task_status.clear()
        task_status["task-1"] = {
            "status": "completed",
            "progress": 100,
            "message": "下载完成",
            "error": None,
            "filename": "demo.mp4",
            "filepath": "/tmp/demo.mp4",
            "download_url": "/api/download/fetch/task-1",
        }

        response = client.get("/api/download/status/task-1")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["download_url"], "/api/download/fetch/task-1")

    def test_agent_chat_demo_mode_returns_stable_trace(self):
        client = TestClient(main.app)

        with patch.object(main, "AGENT_DEMO_MODE", True):
            response = client.post(
                "/api/agent/chat",
                json={
                    "message": "帮我下载这个视频",
                    "session_id": "demo",
                    "context": {"url": "https://example.com/demo"},
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["demo_mode"])
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["perception"]["intent"], "download_video")
        self.assertEqual(body["plan"]["steps"][0]["tool"], "parse_video")
        self.assertEqual(body["execution"]["steps"][1]["tool"], "download_video")
        self.assertEqual(body["reflection"]["status"], "ok")
        self.assertEqual(body["final_video"]["platform"], "BiliBili")
        self.assertTrue(body["final_video"]["available_formats"])
        self.assertIn("展示完成", body["suggested_next_action"])

    def test_health_check_includes_download_dependencies(self):
        client = TestClient(main.app)

        response = client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("python_version", body)
        self.assertIn("download_directory", body)
        self.assertIn("ffmpeg", body)
        self.assertIn("yt_dlp", body)


if __name__ == "__main__":
    unittest.main()
