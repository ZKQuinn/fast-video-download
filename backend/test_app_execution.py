import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app.agent.execution import execute_plan


class AppExecutionTests(unittest.TestCase):
    def test_executes_steps_serially(self):
        calls = []

        def fake_runner(name, **kwargs):
            calls.append((name, kwargs))
            return {"tool": name, "args": kwargs}

        result = execute_plan(
            {
                "goal": "download_video",
                "steps": [
                    {"id": "s1", "tool": "parse_video", "args": {"url": "u"}},
                    {
                        "id": "s2",
                        "tool": "download_video",
                        "args": {"url": "u", "is_audio_only": False},
                    },
                ],
            },
            tool_runner=fake_runner,
        )

        self.assertTrue(result["ok"])
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["steps"]), 2)
        self.assertEqual(calls[0], ("parse_video", {"url": "u"}))
        self.assertEqual(calls[1], ("download_video", {"url": "u", "is_audio_only": False}))

    def test_step_result_shape(self):
        result = execute_plan(
            {
                "goal": "parse_video",
                "steps": [{"id": "s1", "tool": "parse_video", "args": {"url": "u"}}],
            },
            tool_runner=lambda name, **kwargs: {"title": "demo"},
        )

        self.assertEqual(
            result["steps"][0],
            {
                "ok": True,
                "tool": "parse_video",
                "data": {"title": "demo"},
                "error": None,
            },
        )

    def test_stops_on_first_failure(self):
        calls = []

        def failing_runner(name, **kwargs):
            calls.append(name)
            if name == "parse_video":
                raise ValueError("parse failed")
            return {"ok": True}

        result = execute_plan(
            {
                "goal": "download_video",
                "steps": [
                    {"id": "s1", "tool": "parse_video", "args": {"url": "u"}},
                    {"id": "s2", "tool": "download_video", "args": {"url": "u"}},
                ],
            },
            tool_runner=failing_runner,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "parse failed")
        self.assertEqual(calls, ["parse_video"])
        self.assertEqual(len(result["steps"]), 1)


if __name__ == "__main__":
    unittest.main()
