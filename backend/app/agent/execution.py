from typing import Any, Callable

from app.tools.registry import run_tool


ToolRunner = Callable[..., dict[str, Any]]


def execute_plan(
    plan: dict[str, Any],
    tool_runner: ToolRunner = run_tool,
) -> dict[str, Any]:
    """Execute plan steps serially and stop on the first failure."""
    step_results = []

    for step in plan.get("steps", []):
        result = execute_step(step, tool_runner=tool_runner)
        step_results.append(result)
        if not result["ok"]:
            return {
                "ok": False,
                "goal": plan.get("goal"),
                "steps": step_results,
                "error": result["error"],
            }

    return {
        "ok": True,
        "goal": plan.get("goal"),
        "steps": step_results,
        "error": None,
    }


def execute_step(
    step: dict[str, Any],
    tool_runner: ToolRunner = run_tool,
) -> dict[str, Any]:
    tool_name = step.get("tool")
    args = step.get("args") or {}

    try:
        data = tool_runner(tool_name, **args)
        return {
            "ok": True,
            "tool": tool_name,
            "data": data,
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "data": None,
            "error": str(exc),
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
