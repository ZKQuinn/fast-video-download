import os
from typing import Any


def reflect(
    execution_result: dict[str, Any],
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Review execution results and produce a minimal repair plan when possible."""
    failed_step = _find_failed_step(execution_result)
    if failed_step:
        tool = failed_step.get("tool")
        if tool == "parse_video":
            return {
                "status": "needs_repair",
                "reason": failed_step.get("error") or "parse_video failed",
                "repair_plan": _repair_from_plan(plan, "parse_video"),
            }
        if tool == "download_video":
            return {
                "status": "needs_repair",
                "reason": failed_step.get("error") or "download_video failed",
                "repair_plan": _repair_from_plan(plan, "download_video"),
            }
        return {
            "status": "failed",
            "reason": failed_step.get("error") or f"unsupported failed tool: {tool}",
            "repair_plan": [],
        }

    missing_file_reason = _check_download_file(execution_result)
    if missing_file_reason:
        return {
            "status": "needs_repair",
            "reason": missing_file_reason,
            "repair_plan": _repair_from_plan(plan, "download_video"),
        }

    if execution_result.get("ok"):
        return {
            "status": "ok",
            "reason": "execution result satisfies the goal",
            "repair_plan": [],
        }

    return {
        "status": "failed",
        "reason": execution_result.get("error") or "execution failed",
        "repair_plan": [],
    }


def _find_failed_step(execution_result: dict[str, Any]) -> dict[str, Any] | None:
    for step in execution_result.get("steps", []):
        if not step.get("ok", False):
            return step
    return None


def _check_download_file(execution_result: dict[str, Any]) -> str | None:
    for step in execution_result.get("steps", []):
        if step.get("tool") != "download_video" or not step.get("ok"):
            continue

        data = step.get("data") or {}
        filepath = data.get("filepath")
        if not filepath:
            return "download_video result is missing filepath"
        if not os.path.exists(filepath):
            return f"downloaded file does not exist: {filepath}"

    return None


def _repair_from_plan(plan: dict[str, Any] | None, tool_name: str) -> list[dict[str, Any]]:
    if not plan:
        return []

    steps = plan.get("steps", [])
    for index, step in enumerate(steps):
        if step.get("tool") == tool_name:
            return steps[index:]

    return []
