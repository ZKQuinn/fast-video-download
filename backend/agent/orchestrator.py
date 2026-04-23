from agent.execution import execute_plan
from agent.perception import perceive
from agent.planning import create_plan
from agent.reflection import reflect_and_replan


def run_agent(url: str) -> dict:
    """Run url -> perception -> planning -> execution -> reflection."""
    context = perceive(url)
    if not context["url"]:
        return {
            "status": "failed",
            "result": None,
            "plan": None,
            "error": "缺少 URL",
        }

    plan = create_plan(context)
    result = execute_plan(plan, context)
    plans = [plan]

    if not result["ok"]:
        repair_plan = reflect_and_replan(context, plan, result)
        if repair_plan:
            plans.append(repair_plan)
            plan = repair_plan
            result = execute_plan(repair_plan, context)

    if result["ok"]:
        return {
            "status": "completed",
            "result": result["data"],
            "plan": plan,
            "plans": plans,
        }

    return {
        "status": "failed",
        "result": None,
        "plan": plan,
        "plans": plans,
        "error": result["error"],
    }
