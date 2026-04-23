import json

from llm.client import call_llm


def create_plan(context: dict) -> dict:
    """Create a tool-calling plan from perceived context."""
    prompt = (
        "You are planning a video download task. "
        "Return JSON only with the tool to call.\n"
        f"Context: {json.dumps(context, ensure_ascii=False)}"
    )
    plan = call_llm(prompt)

    if not isinstance(plan, dict):
        raise ValueError("LLM returned an invalid plan")
    if "tool" not in plan:
        raise ValueError("Plan is missing required field: tool")

    return plan
