import json
from typing import Any, Protocol

from app.llm.client import LLMClient


ALLOWED_TOOLS = {"parse_video", "download_video"}

PLANNING_PROMPT_TEMPLATE = """\
Create a video-task execution plan from this perception context.

Return JSON only in this exact shape:
{{
  "goal": "download_video|download_audio|parse_video",
  "steps": [
    {{"id": "s1", "tool": "parse_video", "args": {{"url": "..."}}}}
  ],
  "requires_user_confirmation": true
}}

Allowed tools:
- parse_video
- download_video

For download requests, only parse first and wait for the user to choose a format.

Perception context:
{perception_json}
"""


class Planner(Protocol):
    def create_plan(self, perception: dict[str, Any]) -> dict[str, Any]:
        """Create an executable plan from perception output."""


class RuleBasedPlanner:
    """Minimal rule-based planner. Replace with an LLM planner later."""

    def create_plan(self, perception: dict[str, Any]) -> dict[str, Any]:
        intent = perception.get("intent") or "download_video"
        entities = perception.get("entities") or {}
        constraints = perception.get("constraints") or {}
        url = entities.get("url")

        if intent == "parse_video":
            return {
                "goal": "parse_video",
                "steps": [_parse_step("s1", url)],
            }

        if intent == "download_audio":
            return {
                "goal": "download_audio",
                "steps": [_parse_step("s1", url)],
                "requires_user_confirmation": True,
                "recommended_action": "select_audio_format",
            }

        if intent == "download_video":
            return {
                "goal": "download_video",
                "steps": [_parse_step("s1", url)],
                "requires_user_confirmation": True,
                "recommended_action": "select_format",
                "format_hint": constraints.get("format_hint"),
            }

        return {
            "goal": intent,
            "steps": [],
        }


class LLMPlanner:
    """LLM planner with strict JSON validation and rule-based fallback."""

    def __init__(
        self,
        client: LLMClient | None = None,
        fallback: Planner | None = None,
    ):
        self.client = client or LLMClient()
        self.fallback = fallback or RuleBasedPlanner()

    def create_plan(self, perception: dict[str, Any]) -> dict[str, Any]:
        prompt = build_planning_prompt(perception)
        raw_output = self.client.chat(prompt)

        try:
            plan = parse_plan_json(raw_output)
            validate_plan(plan)
            return plan
        except ValueError:
            return self.fallback.create_plan(perception)


def create_plan(perception: dict[str, Any], planner: Planner | None = None) -> dict[str, Any]:
    """Create a structured execution plan from perception output."""
    active_planner = planner or RuleBasedPlanner()
    return active_planner.create_plan(perception)


def build_planning_prompt(perception: dict[str, Any]) -> str:
    return PLANNING_PROMPT_TEMPLATE.format(
        perception_json=json.dumps(perception, ensure_ascii=False, indent=2)
    )


def parse_plan_json(raw_output: str) -> dict[str, Any]:
    if not raw_output or not raw_output.strip():
        raise ValueError("LLM output is empty")

    text = raw_output.strip()
    if text.startswith("```"):
        text = _strip_code_fence(text)

    try:
        plan = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM output is not valid JSON") from exc

    if not isinstance(plan, dict):
        raise ValueError("Plan JSON must be an object")

    return plan


def validate_plan(plan: dict[str, Any]) -> None:
    if not isinstance(plan.get("goal"), str) or not plan["goal"]:
        raise ValueError("Plan must include a non-empty goal")

    steps = plan.get("steps")
    if not isinstance(steps, list):
        raise ValueError("Plan steps must be a list")

    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("Each step must be an object")
        if not isinstance(step.get("id"), str) or not step["id"]:
            raise ValueError("Each step must include id")
        if step.get("tool") not in ALLOWED_TOOLS:
            raise ValueError(f"Unsupported tool: {step.get('tool')}")
        if not isinstance(step.get("args"), dict):
            raise ValueError("Each step must include args object")


def _strip_code_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_step(step_id: str, url: str | None) -> dict[str, Any]:
    return {
        "id": step_id,
        "tool": "parse_video",
        "args": {"url": url},
    }


def _download_step(
    step_id: str,
    url: str | None,
    is_audio_only: bool = False,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "tool": "download_video",
        "args": {
            "url": url,
            "is_audio_only": is_audio_only,
        },
    }
