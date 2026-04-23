from agent.planning import create_plan


def reflect_and_replan(context: dict, plan: dict, execution_result: dict) -> dict | None:
    """Generate one repair plan when execution fails."""
    if execution_result.get("ok"):
        return None

    reflection_context = {
        **context,
        "previous_plan": plan,
        "error": execution_result.get("error"),
        "retry": True,
    }
    return create_plan(reflection_context)
