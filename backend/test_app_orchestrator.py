import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app.agent.orchestrator import run


class AppOrchestratorTests(unittest.TestCase):
    def test_runs_full_pipeline_successfully(self):
        def fake_runner(name, **kwargs):
            if name == "parse_video":
                return {"title": "demo"}
            if name == "download_video":
                return {"filepath": __file__}
            raise ValueError("unexpected tool")

        result = run(
            "帮我下载这个视频 https://example.com/video",
            tool_runner=fake_runner,
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["perception"]["intent"], "download_video")
        self.assertEqual(result["plan"]["goal"], "download_video")
        self.assertTrue(result["execution"]["ok"])
        self.assertEqual(result["reflection"]["status"], "ok")

    def test_returns_needs_repair_when_execution_fails(self):
        def fake_runner(name, **kwargs):
            raise ValueError("tool failed")

        result = run(
            "帮我下载这个视频 https://example.com/video",
            tool_runner=fake_runner,
        )

        self.assertEqual(result["status"], "needs_repair")
        self.assertFalse(result["execution"]["ok"])
        self.assertEqual(result["reflection"]["status"], "needs_repair")
        self.assertTrue(result["reflection"]["repair_plan"])


if __name__ == "__main__":
    unittest.main()
