from typing import Any

from app.agent.execution import ToolRunner, execute_plan
from app.agent.perception import perceive
from app.agent.planning import Planner, create_plan
from app.agent.reflection import reflect
from app.tools.registry import run_tool


def run(
    user_input: str,
    session_context: dict[str, Any] | None = None,
    planner: Planner | None = None,
    tool_runner: ToolRunner = run_tool,
) -> dict[str, Any]:
    """Run perception -> planning -> execution -> reflection for a user request."""
    perception = perceive(user_input, session_context=session_context)
    plan = create_plan(perception, planner=planner)
    execution = execute_plan(plan, tool_runner=tool_runner)
    reflection = reflect(execution, plan=plan)

    return {
        "status": _final_status(reflection),
        "perception": perception,
        "plan": plan,
        "execution": execution,
        "reflection": reflection,
    }


def _final_status(reflection: dict[str, Any]) -> str:
    if reflection.get("status") == "ok":
        return "completed"
    if reflection.get("status") == "needs_repair":
        return "needs_repair"
    return "failed"
