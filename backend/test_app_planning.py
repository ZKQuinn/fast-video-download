import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from app.agent.planning import (
    LLMPlanner,
    build_planning_prompt,
    create_plan,
    parse_plan_json,
    validate_plan,
)


class AppPlanningTests(unittest.TestCase):
    def test_creates_parse_plan(self):
        self.assertEqual(
            create_plan({
                "intent": "parse_video",
                "entities": {"url": "https://example.com/video"},
                "constraints": {},
            }),
            {
                "goal": "parse_video",
                "steps": [
                    {
                        "id": "s1",
                        "tool": "parse_video",
                        "args": {"url": "https://example.com/video"},
                    },
                ],
            },
        )

    def test_creates_download_video_plan(self):
        self.assertEqual(
            create_plan({
                "intent": "download_video",
                "entities": {"url": "https://example.com/video"},
                "constraints": {},
            }),
            {
                "goal": "download_video",
                "steps": [
                    {
                        "id": "s1",
                        "tool": "parse_video",
                        "args": {"url": "https://example.com/video"},
                    },
                ],
                "requires_user_confirmation": True,
                "recommended_action": "select_format",
                "format_hint": None,
            },
        )

    def test_creates_download_audio_plan(self):
        plan = create_plan({
            "intent": "download_audio",
            "entities": {"url": "https://example.com/video"},
            "constraints": {"is_audio_only": True},
        })

        self.assertEqual(plan["goal"], "download_audio")
        self.assertEqual([step["tool"] for step in plan["steps"]], ["parse_video"])
        self.assertTrue(plan["requires_user_confirmation"])

    def test_allows_custom_planner_extension_point(self):
        class FakePlanner:
            def create_plan(self, perception):
                return {"goal": "fake", "steps": []}

        self.assertEqual(
            create_plan({"intent": "download_video"}, planner=FakePlanner()),
            {"goal": "fake", "steps": []},
        )

    def test_llm_planner_returns_valid_json_plan(self):
        class FakeClient:
            def chat(self, prompt):
                return """
                {
                  "goal": "parse_video",
                  "steps": [
                    {
                      "id": "s1",
                      "tool": "parse_video",
                      "args": {"url": "https://example.com/video"}
                    }
                  ]
                }
                """

        plan = LLMPlanner(client=FakeClient()).create_plan({
            "intent": "parse_video",
            "entities": {"url": "https://example.com/video"},
            "constraints": {},
        })

        self.assertEqual(plan["goal"], "parse_video")
        self.assertEqual(plan["steps"][0]["tool"], "parse_video")

    def test_llm_planner_falls_back_on_invalid_json(self):
        class FakeClient:
            def chat(self, prompt):
                return "not json"

        plan = LLMPlanner(client=FakeClient()).create_plan({
            "intent": "download_video",
            "entities": {"url": "https://example.com/video"},
            "constraints": {},
        })

        self.assertEqual(plan["goal"], "download_video")
        self.assertEqual([step["tool"] for step in plan["steps"]], [
            "parse_video",
        ])

    def test_llm_planner_falls_back_on_invalid_tool(self):
        class FakeClient:
            def chat(self, prompt):
                return '{"goal": "bad", "steps": [{"id": "s1", "tool": "delete_file", "args": {}}]}'

        plan = LLMPlanner(client=FakeClient()).create_plan({
            "intent": "parse_video",
            "entities": {"url": "https://example.com/video"},
            "constraints": {},
        })

        self.assertEqual(plan["goal"], "parse_video")
        self.assertEqual(plan["steps"][0]["tool"], "parse_video")

    def test_parse_plan_json_accepts_code_fence(self):
        plan = parse_plan_json('```json\n{"goal": "parse_video", "steps": []}\n```')

        self.assertEqual(plan, {"goal": "parse_video", "steps": []})

    def test_validate_plan_rejects_non_object_args(self):
        with self.assertRaises(ValueError):
            validate_plan({
                "goal": "parse_video",
                "steps": [{"id": "s1", "tool": "parse_video", "args": None}],
            })

    def test_prompt_contains_perception_context(self):
        prompt = build_planning_prompt({
            "intent": "download_audio",
            "entities": {"url": "https://example.com/video"},
            "constraints": {"is_audio_only": True},
        })

        self.assertIn("download_audio", prompt)
        self.assertIn("https://example.com/video", prompt)


if __name__ == "__main__":
    unittest.main()
