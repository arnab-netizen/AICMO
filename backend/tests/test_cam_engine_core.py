"""
Tests for CAM Engine Core Logic (Phase 4).

Tests state machine, safety limits, targets tracking, lead pipeline, and outreach engine.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from aicmo.core.db import Base
from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB, SafetySettingsDB
from aicmo.cam.domain import (
    Campaign,
    Lead,
    LeadStatus,
    LeadSource,
    Channel,
    AttemptStatus,
)
from aicmo.cam.engine.state_machine import (
    initial_status_for_new_lead,
    status_after_enrichment,
    status_after_outreach,
    should_stop_followup,
    compute_next_action_time,
    get_attempt_count,
    advance_attempt_count,
)
from aicmo.cam.engine.safety_limits import (
    get_daily_email_limit,
    remaining_email_quota,
    can_send_email,
    get_today_email_count,
)
from aicmo.cam.engine.targets_tracker import (
    compute_campaign_metrics,
    is_campaign_goal_met,
    should_pause_campaign,
)
from aicmo.cam.engine.lead_pipeline import (
    get_existing_leads_set,
    deduplicate_leads,
    fetch_and_insert_new_leads,
    enrich_and_score_leads,
)
from aicmo.cam.engine.outreach_engine import (
    schedule_due_outreach,
    execute_due_outreach,
    get_outreach_stats,
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
        description="Test campaign for CAM engine",
        target_niche="B2B SaaS",
        active=True,
        service_key="web_design",
        target_clients=10,
        target_mrr=5000.0,
        channels_enabled=["email"],
        max_emails_per_day=20,
        max_outreach_per_day=50,
    )
    test_db.add(campaign)
    test_db.commit()
    return campaign


@pytest.fixture
def test_lead(test_db, test_campaign):
    """Create a test lead."""
    lead = LeadDB(
        campaign_id=test_campaign.id,
        name="John Doe",
        email="john@example.com",
        company="Acme Corp",
        role="CEO",
        status=LeadStatus.NEW,
        source=LeadSource.APOLLO,
    )
    test_db.add(lead)
    test_db.commit()
    return lead


# ═══════════════════════════════════════════════════════════════════════
# STATE MACHINE TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestStateMachine:
    """Tests for state machine transitions."""
    
    def test_initial_status_for_new_lead(self):
        """New leads should have NEW status."""
        lead = Lead(name="Test", email="test@example.com")
        status = initial_status_for_new_lead(lead)
        assert status == LeadStatus.NEW
    
    def test_status_after_enrichment_with_data(self):
        """Lead with enrichment data should be ENRICHED."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            enrichment_data={"company_size": "100-500"},
        )
        status = status_after_enrichment(lead)
        assert status == LeadStatus.ENRICHED
    
    def test_status_after_enrichment_without_data(self):
        """Lead without enrichment data should be NEW."""
        lead = Lead(name="Test", email="test@example.com")
        status = status_after_enrichment(lead)
        assert status == LeadStatus.NEW
    
    def test_status_after_outreach_sent(self):
        """After successful send, should be CONTACTED."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.ENRICHED,
        )
        status = status_after_outreach(lead, AttemptStatus.SENT)
        assert status == LeadStatus.CONTACTED
    
    def test_status_after_outreach_sent_with_high_score(self):
        """High-score lead after send should be QUALIFIED."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.ENRICHED,
            lead_score=0.8,
        )
        status = status_after_outreach(lead, AttemptStatus.SENT)
        assert status == LeadStatus.QUALIFIED
    
    def test_status_after_outreach_failed(self):
        """Failed send should keep current status."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.ENRICHED,
        )
        status = status_after_outreach(lead, AttemptStatus.FAILED)
        assert status == LeadStatus.ENRICHED
    
    def test_should_stop_followup_qualified(self):
        """Should not follow up on QUALIFIED leads."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.QUALIFIED,
        )
        campaign = Campaign(name="Test", target_niche="B2B")
        assert should_stop_followup(lead, campaign)
    
    def test_should_stop_followup_with_dnc_tag(self):
        """Should stop followup if do_not_contact tag present."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.CONTACTED,
            tags=["do_not_contact"],
        )
        campaign = Campaign(name="Test", target_niche="B2B")
        assert should_stop_followup(lead, campaign)
    
    def test_should_not_stop_followup_new_lead(self):
        """Should continue followup on NEW leads."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.NEW,
        )
        campaign = Campaign(name="Test", target_niche="B2B")
        assert not should_stop_followup(lead, campaign)
    
    def test_compute_next_action_time_enrichment(self):
        """Enrichment should be scheduled immediately."""
        lead = Lead(name="Test", email="test@example.com")
        campaign = Campaign(name="Test")
        now = datetime.utcnow()
        
        next_time = compute_next_action_time(lead, campaign, now, "enrichment")
        
        # Should be within 1 minute
        delta = (next_time - now).total_seconds()
        assert 0 < delta < 60
    
    def test_compute_next_action_time_new_lead_followup(self):
        """New lead followup should be soon."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.NEW,
        )
        campaign = Campaign(name="Test")
        now = datetime.utcnow()
        
        next_time = compute_next_action_time(lead, campaign, now, "followup")
        
        # Should be within 1 hour
        delta = (next_time - now).total_seconds()
        assert 0 < delta < 3600
    
    def test_compute_next_action_time_enriched_lead(self):
        """Enriched lead timing should depend on score."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.ENRICHED,
            lead_score=0.2,  # Low score
        )
        campaign = Campaign(name="Test")
        now = datetime.utcnow()
        
        next_time = compute_next_action_time(lead, campaign, now, "followup")
        
        # Low score should schedule further out
        delta = (next_time - now).total_seconds()
        assert delta > 3600  # > 1 hour
    
    def test_compute_next_action_time_contacted_lead(self):
        """Contacted lead should wait 3+ days before followup."""
        lead = Lead(
            name="Test",
            email="test@example.com",
            status=LeadStatus.CONTACTED,
        )
        campaign = Campaign(name="Test")
        now = datetime.utcnow()
        
        next_time = compute_next_action_time(lead, campaign, now, "followup")
        
        # Should be 3+ days
        delta = (next_time - now).total_seconds()
        assert delta > (3 * 86400 - 100)  # ~3 days, allow small variance


# ═══════════════════════════════════════════════════════════════════════
# SAFETY LIMITS TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestSafetyLimits:
    """Tests for safety and rate limiting."""
    
    def test_get_daily_email_limit_from_campaign(self, test_campaign):
        """Should return campaign's max_emails_per_day."""
        limit = get_daily_email_limit(test_campaign)
        assert limit == 20
    
    def test_get_daily_email_limit_default(self, test_db):
        """Should return default limit if not set on campaign."""
        campaign = CampaignDB(
            name="Test",
            active=True,
            channels_enabled=["email"],
            # max_emails_per_day not set
        )
        test_db.add(campaign)
        test_db.commit()
        
        limit = get_daily_email_limit(campaign)
        assert limit == 20  # Default
    
    def test_remaining_email_quota_fresh_campaign(self, test_db, test_campaign):
        """Fresh campaign should have full quota."""
        now = datetime.utcnow()
        quota = remaining_email_quota(test_db, test_campaign.id, now)
        assert quota == 20
    
    def test_remaining_email_quota_after_sends(self, test_db, test_campaign, test_lead):
        """Quota should decrease after sends."""
        now = datetime.utcnow()
        
        # Record 5 sent emails
        for _ in range(5):
            attempt = OutreachAttemptDB(
                campaign_id=test_campaign.id,
                lead_id=test_lead.id,
                channel=Channel.EMAIL,
                status=AttemptStatus.SENT,
            )
            test_db.add(attempt)
        test_db.commit()
        
        quota = remaining_email_quota(test_db, test_campaign.id, now)
        assert quota == 15
    
    def test_can_send_email_active_campaign(self, test_db, test_campaign):
        """Should be able to send to active campaign with quota."""
        now = datetime.utcnow()
        can_send, reason = can_send_email(test_db, test_campaign.id, now)
        assert can_send is True
        assert reason == "OK"
    
    def test_can_send_email_inactive_campaign(self, test_db, test_campaign):
        """Should not send to inactive campaign."""
        test_campaign.active = False
        test_db.commit()
        
        now = datetime.utcnow()
        can_send, reason = can_send_email(test_db, test_campaign.id, now)
        assert can_send is False
    
    def test_can_send_email_quota_exhausted(self, test_db, test_campaign, test_lead):
        """Should not send when quota exhausted."""
        now = datetime.utcnow()
        
        # Fill quota
        for _ in range(20):
            attempt = OutreachAttemptDB(
                campaign_id=test_campaign.id,
                lead_id=test_lead.id,
                channel=Channel.EMAIL,
                status=AttemptStatus.SENT,
            )
            test_db.add(attempt)
        test_db.commit()
        
        can_send, reason = can_send_email(test_db, test_campaign.id, now)
        assert can_send is False
        assert "exhausted" in reason.lower()


# ═══════════════════════════════════════════════════════════════════════
# TARGETS TRACKER TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestTargetsTracker:
    """Tests for campaign goal tracking."""
    
    def test_compute_campaign_metrics_empty(self, test_db, test_campaign):
        """Metrics should be zero for empty campaign."""
        metrics = compute_campaign_metrics(test_db, test_campaign.id)
        assert metrics.total_leads == 0
        assert metrics.status_new == 0
        assert metrics.conversion_rate == 0.0
    
    def test_compute_campaign_metrics_with_leads(self, test_db, test_campaign):
        """Metrics should count leads by status."""
        # Add various leads
        for i in range(5):
            lead = LeadDB(
                campaign_id=test_campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                status=LeadStatus.NEW if i < 3 else LeadStatus.QUALIFIED,
            )
            test_db.add(lead)
        test_db.commit()
        
        metrics = compute_campaign_metrics(test_db, test_campaign.id)
        assert metrics.total_leads == 5
        assert metrics.status_new == 3
        assert metrics.status_qualified == 2
        assert metrics.conversion_rate == 0.4  # 2/5
    
    def test_is_campaign_goal_met_not_met(self, test_db, test_campaign):
        """Goal not met if qualified < target."""
        # Add 2 qualified, but target is 10
        for i in range(2):
            lead = LeadDB(
                campaign_id=test_campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                status=LeadStatus.QUALIFIED,
            )
            test_db.add(lead)
        test_db.commit()
        
        goal_met, reason = is_campaign_goal_met(test_db, test_campaign)
        assert goal_met is False
    
    def test_is_campaign_goal_met_reached(self, test_db, test_campaign):
        """Goal met if qualified >= target."""
        # Add 10 qualified (matches target of 10)
        for i in range(10):
            lead = LeadDB(
                campaign_id=test_campaign.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                status=LeadStatus.QUALIFIED,
            )
            test_db.add(lead)
        test_db.commit()
        
        goal_met, reason = is_campaign_goal_met(test_db, test_campaign)
        assert goal_met is True


# ═══════════════════════════════════════════════════════════════════════
# LEAD PIPELINE TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestLeadPipeline:
    """Tests for lead discovery and enrichment pipeline."""
    
    def test_get_existing_leads_set_empty(self, test_db, test_campaign):
        """Empty campaign should have no existing leads."""
        existing = get_existing_leads_set(test_db, test_campaign.id)
        assert len(existing) == 0
    
    def test_get_existing_leads_set_populated(self, test_db, test_campaign):
        """Should find existing leads by email."""
        lead = LeadDB(
            campaign_id=test_campaign.id,
            name="Test",
            email="test@example.com",
            linkedin_url="https://linkedin.com/in/test",
        )
        test_db.add(lead)
        test_db.commit()
        
        existing = get_existing_leads_set(test_db, test_campaign.id)
        assert f"email:test@example.com" in existing
    
    def test_deduplicate_leads_no_duplicates(self):
        """No duplicates should return all leads."""
        new_leads = [
            Lead(name="A", email="a@example.com", linkedin_url="https://linkedin.com/in/a"),
            Lead(name="B", email="b@example.com", linkedin_url="https://linkedin.com/in/b"),
        ]
        existing = {}
        
        result = deduplicate_leads(new_leads, existing)
        assert len(result) == 2
    
    def test_deduplicate_leads_with_duplicates(self):
        """Duplicate emails should be removed."""
        new_leads = [
            Lead(name="A", email="a@example.com"),
            Lead(name="A2", email="a@example.com"),  # Duplicate
        ]
        existing = {}
        
        result = deduplicate_leads(new_leads, existing)
        assert len(result) == 1


# ═══════════════════════════════════════════════════════════════════════
# OUTREACH ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestOutreachEngine:
    """Tests for outreach scheduling and execution."""
    
    def test_schedule_due_outreach_none_due(self, test_db, test_campaign, test_lead):
        """No leads should be due if next_action_at is in future."""
        test_lead.status = LeadStatus.NEW
        test_lead.next_action_at = datetime.utcnow() + timedelta(hours=1)
        test_db.commit()
        
        now = datetime.utcnow()
        due = schedule_due_outreach(test_db, test_campaign, now)
        assert len(due) == 0
    
    def test_schedule_due_outreach_one_due(self, test_db, test_campaign, test_lead):
        """Should find lead when next_action_at <= now."""
        test_lead.status = LeadStatus.ENRICHED
        test_lead.next_action_at = datetime.utcnow() - timedelta(hours=1)
        test_db.commit()
        
        now = datetime.utcnow()
        due = schedule_due_outreach(test_db, test_campaign, now)
        assert len(due) == 1
        assert due[0].id == test_lead.id
    
    def test_schedule_due_outreach_ignores_inactive(self, test_db, test_campaign, test_lead):
        """Should ignore inactive campaigns."""
        test_campaign.active = False
        test_lead.status = LeadStatus.ENRICHED
        test_lead.next_action_at = datetime.utcnow() - timedelta(hours=1)
        test_db.commit()
        
        now = datetime.utcnow()
        due = schedule_due_outreach(test_db, test_campaign, now)
        assert len(due) == 0
    
    def test_get_outreach_stats(self, test_db, test_campaign, test_lead):
        """Should count outreach attempts by status."""
        # Add various attempts
        for i, status in enumerate([AttemptStatus.SENT, AttemptStatus.SENT, AttemptStatus.FAILED]):
            attempt = OutreachAttemptDB(
                campaign_id=test_campaign.id,
                lead_id=test_lead.id,
                channel=Channel.EMAIL,
                status=status,
            )
            test_db.add(attempt)
        test_db.commit()
        
        stats = get_outreach_stats(test_db, test_campaign.id)
        assert stats["total"] == 3
        assert stats["sent"] == 2
        assert stats["failed"] == 1
        assert stats["skipped"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
