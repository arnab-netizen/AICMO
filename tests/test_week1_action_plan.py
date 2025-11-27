"""Tests for Week 1 Action Plan feature."""

import pytest


def test_week1_plan_has_7_items():
    """Test that action plan has exactly 7 daily tasks."""
    from backend.generators.action.week1_action_plan import generate_week1_action_plan

    report = {
        "brand": "Test Cafe",
        "goals": ["increase sales"],
    }

    result = generate_week1_action_plan(report)

    assert "week1_plan" in result
    plan = result["week1_plan"]
    assert len(plan) == 7
    assert all(isinstance(task, str) for task in plan)


def test_week1_plan_customization():
    """Test that action plan incorporates brand and goal information."""
    from backend.generators.action.week1_action_plan import generate_week1_action_plan

    report = {
        "brand": "My Custom Brand",
        "goals": ["boost brand awareness"],
    }

    result = generate_week1_action_plan(report)
    plan = result["week1_plan"]

    # First task should mention the brand name or goal
    first_task = plan[0]
    assert any(word.lower() in first_task.lower() for word in ["boost", "brand", "awareness"])


def test_week1_plan_fallback_values():
    """Test that action plan handles missing brand/goal gracefully."""
    from backend.generators.action.week1_action_plan import generate_week1_action_plan

    report = {}  # Empty report

    result = generate_week1_action_plan(report)

    assert "week1_plan" in result
    assert len(result["week1_plan"]) == 7
    # Should still work with placeholder text
    assert all(task for task in result["week1_plan"])


def test_week1_plan_with_string_goals():
    """Test that action plan handles goals as string (not list)."""
    from backend.generators.action.week1_action_plan import generate_week1_action_plan

    report = {
        "brand": "Test Brand",
        "goals": "Increase revenue",  # String, not list
    }

    result = generate_week1_action_plan(report)

    assert "week1_plan" in result
    assert len(result["week1_plan"]) == 7


def test_week1_plan_structure():
    """Test that all tasks are concrete and actionable."""
    from backend.generators.action.week1_action_plan import generate_week1_action_plan

    result = generate_week1_action_plan({"brand": "Test"})
    plan = result["week1_plan"]

    # Each task should start with "Day N:"
    for i, task in enumerate(plan, 1):
        assert task.startswith(f"Day {i}:")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
