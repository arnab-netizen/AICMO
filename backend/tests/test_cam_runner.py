"""
Tests for CAM Phase 5: Worker/Runner Wiring.

Tests the autonomous CAM runner that orchestrates the complete cycle.
"""

import pytest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from aicmo.core.db import Base
from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.cam.domain import LeadStatus, LeadSource, Channel, AttemptStatus
from aicmo.cam.auto_runner import (
    run_cam_cycle_for_campaign,
    run_cam_cycle_for_all,
)


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session_local = sessionmaker(bind=engine)
    db = Session_local()
    yield db
    db.close()


@pytest.fixture
def test_campaign(test_db):
    """Create a test campaign."""
    campaign = CampaignDB(
        name="Test Campaign",
        target_niche="B2B SaaS",
        active=True,
        service_key="web_design",
        target_clients=5,
        channels_enabled=["email"],
        max_emails_per_day=20,
    )
    test_db.add(campaign)
    test_db.commit()
    return campaign


@pytest.fixture
def test_campaign_with_leads(test_db, test_campaign):
    """Create a campaign with some test leads."""
    # Add 3 leads
    for i in range(3):
        lead = LeadDB(
            campaign_id=test_campaign.id,
            name=f"Lead {i}",
            email=f"lead{i}@example.com",
            company=f"Company {i}",
            status=LeadStatus.NEW,
            source=LeadSource.APOLLO,
        )
        test_db.add(lead)
    test_db.commit()
    return test_campaign


# ═══════════════════════════════════════════════════════════════════════
# SINGLE CAMPAIGN CYCLE TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestSingleCampaignCycle:
    """Tests for single campaign CAM cycle."""
    
    def test_run_cam_cycle_campaign_not_found(self, test_db):
        """Should return error if campaign doesn't exist."""
        result = run_cam_cycle_for_campaign(test_db, 999, dry_run=True)
        assert "error" in result
    
    def test_run_cam_cycle_inactive_campaign(self, test_db, test_campaign):
        """Should skip inactive campaigns."""
        test_campaign.active = False
        test_db.commit()
        
        result = run_cam_cycle_for_campaign(test_db, test_campaign.id, dry_run=True)
        assert result["status"] == "inactive"
    
    def test_run_cam_cycle_with_leads(self, test_db, test_campaign_with_leads):
        """Should process leads in a cycle."""
        result = run_cam_cycle_for_campaign(
            test_db,
            test_campaign_with_leads.id,
            dry_run=True,
        )
        
        # Should have stats
        assert result["campaign_id"] == test_campaign_with_leads.id
        assert "leads_discovered" in result
        assert "leads_enriched" in result
        assert "outreach_sent" in result
        assert isinstance(result["errors"], list)
    
    def test_run_cam_cycle_returns_dict(self, test_db, test_campaign):
        """Should always return a dictionary with stats."""
        result = run_cam_cycle_for_campaign(test_db, test_campaign.id, dry_run=True)
        assert isinstance(result, dict)
        assert "campaign_id" in result
        assert "campaign_name" in result


# ═══════════════════════════════════════════════════════════════════════
# MULTI-CAMPAIGN ORCHESTRATION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestMultiCampaignOrchestration:
    """Tests for running CAM cycle for all campaigns."""
    
    def test_run_all_empty_campaigns(self, test_db):
        """Should handle no active campaigns gracefully."""
        result = run_cam_cycle_for_all(test_db, dry_run=True)
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_run_all_single_campaign(self, test_db, test_campaign):
        """Should run cycle for single active campaign."""
        result = run_cam_cycle_for_all(test_db, dry_run=True)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["campaign_id"] == test_campaign.id
    
    def test_run_all_multiple_campaigns(self, test_db):
        """Should run cycle for all active campaigns."""
        # Create 3 campaigns
        for i in range(3):
            campaign = CampaignDB(
                name=f"Campaign {i}",
                active=True,
                channels_enabled=["email"],
            )
            test_db.add(campaign)
        test_db.commit()
        
        result = run_cam_cycle_for_all(test_db, dry_run=True)
        assert len(result) == 3
    
    def test_run_all_ignores_inactive(self, test_db):
        """Should only run for active campaigns."""
        # Create 2 active, 1 inactive
        for i in range(2):
            campaign = CampaignDB(
                name=f"Active {i}",
                active=True,
                channels_enabled=["email"],
            )
            test_db.add(campaign)
        
        inactive = CampaignDB(
            name="Inactive",
            active=False,
            channels_enabled=["email"],
        )
        test_db.add(inactive)
        test_db.commit()
        
        result = run_cam_cycle_for_all(test_db, dry_run=True)
        assert len(result) == 2
    
    def test_run_all_continues_on_error(self, test_db):
        """Should continue with other campaigns if one errors."""
        # This test just verifies that exceptions are caught
        # and don't crash the entire run
        
        # Create 2 campaigns
        campaigns = []
        for i in range(2):
            campaign = CampaignDB(
                name=f"Campaign {i}",
                active=True,
                channels_enabled=["email"],
            )
            test_db.add(campaign)
            campaigns.append(campaign)
        test_db.commit()
        
        # Run should complete without crashing
        result = run_cam_cycle_for_all(test_db, dry_run=True)
        assert len(result) == 2
        # Both should have results (no exceptions)
        assert all("campaign_id" in r for r in result)


# ═══════════════════════════════════════════════════════════════════════
# DRY RUN TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestDryRun:
    """Tests for dry-run behavior (no real emails sent)."""
    
    def test_dry_run_true_by_default(self, test_db, test_campaign_with_leads):
        """dry_run should default to True."""
        result = run_cam_cycle_for_campaign(
            test_db,
            test_campaign_with_leads.id,
        )
        # Should not raise, should complete normally
        assert "campaign_id" in result
    
    def test_dry_run_explicit_false(self, test_db, test_campaign_with_leads):
        """Should support dry_run=False (but won't send in test without gateway)."""
        result = run_cam_cycle_for_campaign(
            test_db,
            test_campaign_with_leads.id,
            dry_run=False,
        )
        # Should still complete (gateway errors are caught)
        assert "campaign_id" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
