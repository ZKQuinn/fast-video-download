import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app.agent.reflection import reflect


PLAN = {
    "goal": "download_video",
    "steps": [
        {"id": "s1", "tool": "parse_video", "args": {"url": "u"}},
        {"id": "s2", "tool": "download_video", "args": {"url": "u"}},
    ],
}


class AppReflectionTests(unittest.TestCase):
    def test_ok_when_download_file_exists(self):
        with tempfile.NamedTemporaryFile() as file:
            result = reflect(
                {
                    "ok": True,
                    "goal": "download_video",
                    "steps": [
                        {
                            "ok": True,
                            "tool": "download_video",
                            "data": {"filepath": file.name},
                            "error": None,
                        },
                    ],
                    "error": None,
                },
                PLAN,
            )

        self.assertEqual(result, {
            "status": "ok",
            "reason": "execution result satisfies the goal",
            "repair_plan": [],
        })

    def test_parse_failure_needs_repair_from_parse_step(self):
        result = reflect(
            {
                "ok": False,
                "goal": "download_video",
                "steps": [
                    {
                        "ok": False,
                        "tool": "parse_video",
                        "data": None,
                        "error": "parse failed",
                    },
                ],
                "error": "parse failed",
            },
            PLAN,
        )

        self.assertEqual(result["status"], "needs_repair")
        self.assertEqual(result["reason"], "parse failed")
        self.assertEqual(result["repair_plan"], PLAN["steps"])

    def test_download_failure_needs_repair_from_download_step(self):
        result = reflect(
            {
                "ok": False,
                "goal": "download_video",
                "steps": [
                    {
                        "ok": True,
                        "tool": "parse_video",
                        "data": {"title": "demo"},
                        "error": None,
                    },
                    {
                        "ok": False,
                        "tool": "download_video",
                        "data": None,
                        "error": "download failed",
                    },
                ],
                "error": "download failed",
            },
            PLAN,
        )

        self.assertEqual(result["status"], "needs_repair")
        self.assertEqual(result["reason"], "download failed")
        self.assertEqual(result["repair_plan"], [PLAN["steps"][1]])

    def test_missing_download_file_needs_repair(self):
        result = reflect(
            {
                "ok": True,
                "goal": "download_video",
                "steps": [
                    {
                        "ok": True,
                        "tool": "download_video",
                        "data": {"filepath": "/tmp/file-that-should-not-exist.mp4"},
                        "error": None,
                    },
                ],
                "error": None,
            },
            PLAN,
        )

        self.assertEqual(result["status"], "needs_repair")
        self.assertIn("does not exist", result["reason"])
        self.assertEqual(result["repair_plan"], [PLAN["steps"][1]])


if __name__ == "__main__":
    unittest.main()
