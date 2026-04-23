import os
import sys
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))

import main
from agent.perception import perceive
from agent.planning import create_plan
from tools.registry import get_tool


class AgentTests(unittest.TestCase):
    def test_perception_normalizes_url(self):
        self.assertEqual(
            perceive(" https://example.com/video "),
            {"url": "https://example.com/video", "intent": "download_video"},
        )

    def test_planning_returns_download_tool(self):
        self.assertEqual(
            create_plan({"url": "https://example.com/video", "intent": "download_video"}),
            {"tool": "download_video"},
        )

    def test_registry_returns_download_tool(self):
        self.assertTrue(callable(get_tool("download_video")))

    def test_agent_api_missing_url_returns_400(self):
        client = TestClient(main.app)
        response = client.post("/api/agent/run", json={})
        self.assertEqual(response.status_code, 400)

    def test_orchestrator_replans_once_after_failure(self):
        import agent.orchestrator as orchestrator

        calls = []

        def fake_execute(plan, context):
            calls.append(plan)
            if len(calls) == 1:
                return {
                    "ok": False,
                    "tool": plan["tool"],
                    "data": None,
                    "error": "forced failure",
                }
            return {
                "ok": True,
                "tool": plan["tool"],
                "data": {"filepath": "/tmp/demo.mp4"},
                "error": None,
            }

        with patch.object(orchestrator, "execute_plan", side_effect=fake_execute):
            result = orchestrator.run_agent("https://example.com/video")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["plans"]), 2)


if __name__ == "__main__":
    unittest.main()
