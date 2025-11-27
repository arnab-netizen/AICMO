"""Week 1 Action Plan generator."""

from typing import Dict, Any, List


def generate_week1_action_plan(report_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Generate a simple Week 1 action checklist based on existing report content.

    This creates 7 actionable daily tasks that operators can execute immediately.
    Uses report context (brand, goals, etc.) to customize the tasks.

    Args:
        report_data: Full report dict with brand, goals, and other context

    Returns:
        Dict with key 'week1_plan' -> list of 7 string tasks
    """
    # Extract main goal from various possible keys
    main_goal = ""
    goals = report_data.get("goals") or report_data.get("campaign_goals") or []
    if isinstance(goals, list) and goals:
        main_goal = goals[0]
    elif isinstance(goals, str):
        main_goal = goals

    tasks: List[str] = [
        f"Day 1: Publish the first priority content piece aligned with your main goal: {main_goal or 'campaign objective'}.",
        "Day 2: Reply thoughtfully to 5 recent Google Reviews or social comments.",
        "Day 3: Record one short-form video (Reel/Short) based on a high-impact content idea from this report.",
        "Day 4: Update your profile bio, cover, and highlights as per the brand positioning in this report.",
        "Day 5: Run one engagement activity (poll, question sticker, or giveaway) to boost interaction.",
        "Day 6: Reach out to at least 5 past customers with a personalised offer or message.",
        "Day 7: Review the week's performance and note 3 learnings to refine content for next week.",
    ]

    return {"week1_plan": tasks}
