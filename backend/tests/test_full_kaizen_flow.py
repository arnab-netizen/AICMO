"""
W1: Integration test for unified Kaizen flow wiring all subsystems.

Tests that Social Intelligence, Analytics, Client Portal, and PM
are all called and produce valid outputs in the orchestrated flow.
"""

import pytest
from datetime import datetime
from aicmo.domain.intake import ClientIntake
from aicmo.delivery.kaizen_orchestrator import KaizenOrchestrator
from aicmo.social.domain import TrendAnalysis
from aicmo.analytics.domain import PerformanceDashboard
from aicmo.portal.domain import ApprovalRequest, ApprovalStatus
from aicmo.pm.domain import Task, TaskStatus


@pytest.fixture
def sample_intake() -> ClientIntake:
    """Create sample client intake for testing."""
    return ClientIntake(
        brand_name="Test Brand Co",
        industry="Technology",
        budget=50000.0,
        timeline_weeks=8,
        target_audience="Tech-savvy professionals aged 25-45",
        business_goals="Increase brand awareness and generate qualified leads",
        contact_email="client@testbrand.com",
        pain_points="Low brand recognition in competitive market"
    )


def test_unified_flow_wires_all_subsystems(sample_intake):
    """
    W1: Test that unified flow calls all subsystems and returns valid outputs.
    
    Verifies:
    - Strategy & creatives exist (baseline)
    - Social intel results exist (W1)
    - Analytics dashboard exists (W1)
    - PM tasks exist (W1)
    - Approval request exists (W1)
    """
    orchestrator = KaizenOrchestrator()
    
    # Run unified flow
    result = orchestrator.run_full_kaizen_flow_for_project(
        intake=sample_intake,
        project_id="test-project-123",
        total_budget=50000.0,
        skip_kaizen=True  # Skip for deterministic test
    )
    
    # Assert basic metadata
    assert result["brand_name"] == "Test Brand Co"
    assert result["project_id"] == "test-project-123"
    assert result["total_budget"] == 50000.0
    assert "execution_time_seconds" in result
    assert result["execution_time_seconds"] > 0
    
    # Assert subsystems wired list
    assert "subsystems_wired" in result
    expected_subsystems = [
        "strategy", "brand", "social", "media", 
        "analytics", "portal", "pm", "creatives"
    ]
    assert result["subsystems_wired"] == expected_subsystems
    
    # W1 Focus: Verify the 4 previously unwired subsystems are now called
    # Strategy is optional (requires LLM), so we focus on brand/media/creatives as baseline
    
    # Baseline: Brand core and positioning exist
    assert "brand_core" in result
    assert result["brand_core"] is not None
    assert hasattr(result["brand_core"], "purpose")
    
    assert "brand_positioning" in result
    assert result["brand_positioning"] is not None
    assert hasattr(result["brand_positioning"], "target_audience")
    
    # Baseline: Media plan exists
    assert "media_plan" in result
    assert result["media_plan"] is not None
    assert hasattr(result["media_plan"], "channels")
    assert len(result["media_plan"].channels) >= 2
    
    # Baseline: Creatives exist
    assert "creatives" in result
    assert result["creatives"] is not None
    
    # W1: Social Intelligence - trend analysis exists
    assert "social_trends" in result
    social_trends = result["social_trends"]
    assert isinstance(social_trends, TrendAnalysis)
    assert hasattr(social_trends, "emerging_trends")
    assert isinstance(social_trends.emerging_trends, list)
    # Trends can be empty but structure must be correct
    assert hasattr(social_trends, "brand_name")
    assert social_trends.brand_name == "Test Brand Co"
    
    # W1: Analytics - performance dashboard exists
    assert "analytics_dashboard" in result
    analytics = result["analytics_dashboard"]
    assert isinstance(analytics, PerformanceDashboard)
    assert hasattr(analytics, "current_metrics")
    assert isinstance(analytics.current_metrics, dict)
    assert len(analytics.current_metrics) > 0  # Should have some metrics
    assert hasattr(analytics, "brand_name")
    assert analytics.brand_name == "Test Brand Co"
    
    # W1: Client Portal - approval request exists
    assert "approval_request" in result
    approval = result["approval_request"]
    assert isinstance(approval, ApprovalRequest)
    assert approval.brand_name == "Test Brand Co"
    assert approval.status == ApprovalStatus.PENDING
    assert approval.asset_name == "Test Brand Co Strategy Document"
    assert len(approval.assigned_reviewers) > 0
    assert hasattr(approval, "request_id")
    assert len(approval.request_id) > 0
    
    # W1: Project Management - tasks exist
    assert "pm_tasks" in result
    pm_tasks = result["pm_tasks"]
    assert isinstance(pm_tasks, list)
    assert len(pm_tasks) >= 3  # Strategy review, creative dev, media launch
    
    for task in pm_tasks:
        assert isinstance(task, Task)
        assert task.brand_name == "Test Brand Co"
        assert task.project_id == "test-project-123"
        assert task.status == TaskStatus.NOT_STARTED
        assert len(task.title) > 0
        assert len(task.description) > 0
        assert hasattr(task, "task_id")
        assert len(task.task_id) > 0
        assert task.estimated_hours is not None
        assert task.estimated_hours > 0
    
    # Verify specific tasks created
    task_titles = [t.title for t in pm_tasks]
    assert "Review and approve strategy document" in task_titles
    assert "Develop creative assets" in task_titles
    assert "Launch media campaign" in task_titles


def test_unified_flow_with_kaizen_context(sample_intake):
    """
    Test that unified flow works with Kaizen context enabled.
    
    Should not crash even if no historical data exists.
    """
    orchestrator = KaizenOrchestrator()
    
    result = orchestrator.run_full_kaizen_flow_for_project(
        intake=sample_intake,
        project_id="test-project-456",
        total_budget=30000.0,
        client_id=999,
        skip_kaizen=False  # Enable Kaizen
    )
    
    assert result["kaizen_enabled"] is True
    assert "kaizen_insights_used" in result
    # May be True or False depending on historical data
    assert isinstance(result["kaizen_insights_used"], bool)
    
    # All subsystems should still be present
    assert "social_trends" in result
    assert "analytics_dashboard" in result
    assert "approval_request" in result
    assert "pm_tasks" in result


def test_unified_flow_execution_time_reasonable(sample_intake):
    """
    Test that unified flow completes in reasonable time.
    
    With 8 subsystems, should complete in under 5 seconds.
    """
    orchestrator = KaizenOrchestrator()
    
    result = orchestrator.run_full_kaizen_flow_for_project(
        intake=sample_intake,
        project_id="test-perf-789",
        total_budget=10000.0,
        skip_kaizen=True
    )
    
    execution_time = result["execution_time_seconds"]
    assert execution_time < 5.0, f"Flow took {execution_time}s, expected < 5s"


def test_unified_flow_no_empty_placeholders(sample_intake):
    """
    Test that unified flow outputs don't contain obvious placeholders.
    
    Note: This is a basic check. Full validation layer comes in W3.
    """
    orchestrator = KaizenOrchestrator()
    
    result = orchestrator.run_full_kaizen_flow_for_project(
        intake=sample_intake,
        project_id="test-validation-001",
        total_budget=25000.0,
        skip_kaizen=True
    )
    
    # Check brand core has values
    brand_core = result["brand_core"]
    assert brand_core.purpose
    assert len(brand_core.purpose) > 10  # Meaningful content
    assert brand_core.values
    assert len(brand_core.values) >= 3
    
    # Check media plan has real budgets
    media_plan = result["media_plan"]
    total_allocated = sum(ch.budget_allocated for ch in media_plan.channels)
    assert total_allocated > 0
    assert abs(total_allocated - 25000.0) < 0.01  # Should match input budget
    
    # Check PM tasks have meaningful content
    for task in result["pm_tasks"]:
        assert task.title
        assert len(task.title) > 5
        assert task.description
        assert len(task.description) > 10
        assert "TBD" not in task.description
    
    # Check approval request has valid URL
    approval = result["approval_request"]
    assert approval.asset_url
    assert approval.asset_url.startswith("http")
    assert "test-validation-001" in approval.asset_url  # Project ID in URL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
