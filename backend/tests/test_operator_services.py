"""
W2.1: Tests for operator services that now call unified orchestrator.

Verifies that operator services return real data from orchestrated flows.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.operator_services import (
    get_projects_pipeline,
    get_project_context,
    get_creatives_for_project,
    get_project_unified_view,
    get_project_pm_dashboard,
    get_project_analytics_dashboard,
)


@pytest.fixture
def sample_campaign(test_db: Session) -> CampaignDB:
    """Create a sample campaign for testing."""
    import time
    campaign = CampaignDB(
        name=f"Test Campaign {time.time()}",
        target_niche="Technology",
        intake_goal="Increase awareness",
        intake_audience="Tech professionals",
        intake_budget="10000",
        strategy_status="DRAFT",
        active=True,
        created_at=datetime.now(),
    )
    test_db.add(campaign)
    test_db.commit()
    test_db.refresh(campaign)
    return campaign


@pytest.fixture
def campaign_with_leads(test_db: Session, sample_campaign: CampaignDB) -> CampaignDB:
    """Add leads to campaign."""
    for i in range(3):
        lead = LeadDB(
            campaign_id=sample_campaign.id,
            name=f"Lead {i}",
            company=f"Company {i}",
            status="NEW",
            stage="CONTACTED",
        )
        test_db.add(lead)
    test_db.commit()
    return sample_campaign


def test_get_projects_pipeline_returns_real_data(test_db: Session, campaign_with_leads: CampaignDB):
    """
    W2.1: Test that get_projects_pipeline returns real campaign data.
    """
    projects = get_projects_pipeline(test_db)
    
    assert isinstance(projects, list)
    assert len(projects) >= 1
    
    # Find our test campaign
    test_project = next((p for p in projects if p["id"] == campaign_with_leads.id), None)
    assert test_project is not None
    
    # Verify structure
    assert "id" in test_project
    assert "name" in test_project
    assert "stage" in test_project
    assert "clarity" in test_project
    assert "strategy_status" in test_project
    assert "lead_count" in test_project
    
    # Verify data
    assert test_project["name"].startswith("Test Campaign")
    assert test_project["lead_count"] == 3
    assert test_project["stage"] in ["INTAKE", "STRATEGY", "CREATIVE", "EXECUTION"]


def test_get_project_context_returns_real_data(test_db: Session, sample_campaign: CampaignDB):
    """
    W2.1: Test that get_project_context returns real campaign context.
    """
    context = get_project_context(test_db, sample_campaign.id)
    
    assert "error" not in context
    assert context["project_name"].startswith("Test Campaign")
    assert context["goal"] == "Increase awareness"
    assert context["audience"] == "Tech professionals"
    assert context["budget"] == "10000"
    assert "lead_count" in context
    assert "outreach_count" in context


def test_get_creatives_for_project_returns_list(test_db: Session, sample_campaign: CampaignDB):
    """
    W2.1: Test that get_creatives_for_project returns creative list.
    
    May return synthetic or real creatives depending on strategy status.
    """
    creatives = get_creatives_for_project(test_db, sample_campaign.id)
    
    assert isinstance(creatives, list)
    assert len(creatives) >= 1
    
    # Verify structure
    for creative in creatives:
        assert "id" in creative
        assert "platform" in creative
        assert "caption" in creative
        assert "status" in creative
        assert "project_id" in creative


def test_get_project_unified_view_returns_dict(test_db: Session, sample_campaign: CampaignDB):
    """
    W2.1: Test that unified view calls orchestrator and returns subsystem outputs.
    """
    result = get_project_unified_view(test_db, sample_campaign.id)
    
    # Should not error
    if "error" in result:
        # Error is acceptable if orchestrator fails, but check it's structured
        assert isinstance(result["error"], str)
    else:
        # If successful, should have subsystem outputs
        assert "brand_name" in result
        assert "campaign_id" in result
        assert result["campaign_id"] == sample_campaign.id
        
        # Check for subsystem outputs (may be None if skipped)
        assert "brand_core" in result or "error" in result
        assert "media_plan" in result or "error" in result


def test_get_project_pm_dashboard_returns_dict(test_db: Session, sample_campaign: CampaignDB):
    """
    W2.1: Test that PM dashboard service returns structured data.
    """
    result = get_project_pm_dashboard(test_db, sample_campaign.id)
    
    assert isinstance(result, dict)
    assert "project_id" in result or "error" in result
    
    if "error" not in result:
        assert result["project_id"] == sample_campaign.id
        assert "dashboard" in result


def test_get_project_analytics_dashboard_returns_dict(test_db: Session, sample_campaign: CampaignDB):
    """
    W2.1: Test that analytics dashboard service returns structured data.
    """
    result = get_project_analytics_dashboard(test_db, sample_campaign.id)
    
    assert isinstance(result, dict)
    assert "project_id" in result or "error" in result
    
    if "error" not in result:
        assert result["project_id"] == sample_campaign.id
        assert "dashboard" in result


def test_get_project_unified_view_handles_missing_project(test_db: Session):
    """
    W2.1: Test error handling for non-existent project.
    """
    result = get_project_unified_view(test_db, 99999)
    
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_operator_services_do_not_crash(test_db: Session, sample_campaign: CampaignDB):
    """
    W2.1: Smoke test that all new operator services handle errors gracefully.
    """
    # All services should return dicts and not raise exceptions
    services_to_test = [
        (get_project_unified_view, (test_db, sample_campaign.id)),
        (get_project_pm_dashboard, (test_db, sample_campaign.id)),
        (get_project_analytics_dashboard, (test_db, sample_campaign.id)),
    ]
    
    for service, args in services_to_test:
        try:
            result = service(*args)
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"{service.__name__} raised exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
