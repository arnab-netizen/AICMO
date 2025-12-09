"""
Review Queue Engine Tests — Phase 9

Integration tests for human-in-the-loop control system.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.cam.db_models import Base, LeadDB, CampaignDB
from aicmo.cam.domain import LeadStatus
from aicmo.cam.engine.review_queue import (
    get_review_queue,
    approve_review_task,
    reject_review_task,
    flag_lead_for_review,
    ReviewTask,
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def campaign(db_session):
    """Create a test campaign."""
    campaign = CampaignDB(
        name="Test Campaign",
        description="For testing review queue",
        status="active",
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest.fixture
def lead(db_session, campaign):
    """Create a test lead."""
    lead = LeadDB(
        campaign_id=campaign.id,
        name="Test Lead",
        email="test@example.com",
        company="Test Corp",
        status=LeadStatus.INTERESTED,
        lead_score=85.0,
        requires_human_review=False,
    )
    db_session.add(lead)
    db_session.commit()
    return lead


class TestReviewQueue:
    """Test review queue core functionality."""
    
    def test_flag_lead_for_review(self, db_session, lead):
        """Test flagging a lead for review."""
        success = flag_lead_for_review(
            lead.id,
            db_session,
            review_type="MESSAGE",
            reason="High-value prospect",
        )
        
        assert success
        
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert refreshed_lead.requires_human_review
        assert refreshed_lead.review_type == "MESSAGE"
        assert refreshed_lead.review_reason == "High-value prospect"
    
    def test_get_review_queue(self, db_session, campaign, lead):
        """Test retrieving review queue."""
        # Flag multiple leads
        flag_lead_for_review(lead.id, db_session, "MESSAGE", "Reason 1")
        
        lead2 = LeadDB(
            campaign_id=campaign.id,
            name="Test Lead 2",
            email="test2@example.com",
            company="Test Corp 2",
            status=LeadStatus.INTERESTED,
            requires_human_review=True,
            review_type="PROPOSAL",
            review_reason="Custom proposal needed",
        )
        db_session.add(lead2)
        db_session.commit()
        
        # Retrieve queue
        tasks = get_review_queue(db_session)
        
        assert len(tasks) == 2
        assert tasks[0].review_type == "MESSAGE"
        assert tasks[1].review_type == "PROPOSAL"
    
    def test_approve_review_task(self, db_session, lead):
        """Test approving a review task."""
        # Flag for review first
        flag_lead_for_review(lead.id, db_session, "MESSAGE", "Test reason")
        
        # Approve
        success = approve_review_task(lead.id, db_session, action="approve")
        assert success
        
        # Verify flag cleared
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert not refreshed_lead.requires_human_review
        assert refreshed_lead.review_type is None
        assert "[REVIEW] Approved" in refreshed_lead.notes
    
    def test_skip_review_task(self, db_session, lead):
        """Test skipping a review task."""
        # Flag for review
        flag_lead_for_review(lead.id, db_session, "MESSAGE", "Test reason")
        
        # Skip
        success = approve_review_task(lead.id, db_session, action="skip")
        assert success
        
        # Verify marked as LOST
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert not refreshed_lead.requires_human_review
        assert refreshed_lead.status == LeadStatus.LOST
        assert "operator_skip" in refreshed_lead.tags
    
    def test_reject_review_task(self, db_session, lead):
        """Test rejecting a review task."""
        # Flag for review
        flag_lead_for_review(lead.id, db_session, "PROPOSAL", "Custom proposal")
        
        # Reject
        success = reject_review_task(
            lead.id,
            db_session,
            reason="Not a fit for product",
        )
        assert success
        
        # Verify marked as LOST with reject tag
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert not refreshed_lead.requires_human_review
        assert refreshed_lead.status == LeadStatus.LOST
        assert "operator_reject" in refreshed_lead.tags
        assert "Not a fit for product" in refreshed_lead.notes
    
    def test_review_task_data_structure(self, lead):
        """Test ReviewTask data structure."""
        task = ReviewTask(
            lead_id=lead.id,
            lead_name="John Doe",
            lead_company="Acme Corp",
            lead_email="john@acme.com",
            review_type="MESSAGE",
            review_reason="High-value prospect",
            suggested_action="send_custom_offer",
            lead_score=92.5,
        )
        
        task_dict = task.to_dict()
        assert task_dict["lead_id"] == lead.id
        assert task_dict["lead_name"] == "John Doe"
        assert task_dict["review_type"] == "MESSAGE"
        assert task_dict["lead_score"] == 92.5
        assert task_dict["created_at"] is not None
    
    def test_filter_review_queue_by_campaign(self, db_session):
        """Test filtering review queue by campaign."""
        # Create two campaigns
        campaign1 = CampaignDB(name="Campaign 1", status="active")
        campaign2 = CampaignDB(name="Campaign 2", status="active")
        db_session.add_all([campaign1, campaign2])
        db_session.commit()
        
        # Create leads in each campaign
        lead1 = LeadDB(
            campaign_id=campaign1.id,
            name="Lead 1",
            email="lead1@example.com",
            status=LeadStatus.INTERESTED,
            requires_human_review=True,
            review_type="MESSAGE",
        )
        lead2 = LeadDB(
            campaign_id=campaign2.id,
            name="Lead 2",
            email="lead2@example.com",
            status=LeadStatus.INTERESTED,
            requires_human_review=True,
            review_type="PROPOSAL",
        )
        db_session.add_all([lead1, lead2])
        db_session.commit()
        
        # Filter by campaign1
        tasks = get_review_queue(db_session, campaign_id=campaign1.id)
        
        assert len(tasks) == 1
        assert tasks[0].lead_id == lead1.id
    
    def test_nonexistent_lead_handling(self, db_session):
        """Test graceful handling of nonexistent leads."""
        success = approve_review_task(9999, db_session, action="approve")
        assert not success
        
        success = reject_review_task(9999, db_session, reason="Not found")
        assert not success


class TestReviewQueueEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_review_queue_empty(self, db_session, campaign):
        """Test getting queue when no tasks exist."""
        tasks = get_review_queue(db_session)
        assert tasks == []
    
    def test_double_flag_overwrites(self, db_session, campaign, lead):
        """Test that flagging twice overwrites previous reason."""
        flag_lead_for_review(lead.id, db_session, "MESSAGE", "Reason 1")
        flag_lead_for_review(lead.id, db_session, "PROPOSAL", "Reason 2")
        
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        assert refreshed_lead.review_type == "PROPOSAL"
        assert refreshed_lead.review_reason == "Reason 2"
    
    def test_notes_accumulation(self, db_session, lead):
        """Test that notes accumulate during review lifecycle."""
        original_notes = lead.notes or ""
        
        flag_lead_for_review(lead.id, db_session, "MESSAGE", "Initial flag")
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        notes_after_flag = refreshed_lead.notes
        
        approve_review_task(lead.id, db_session, action="approve")
        refreshed_lead = db_session.query(LeadDB).filter(LeadDB.id == lead.id).first()
        notes_after_approve = refreshed_lead.notes
        
        assert "[FLAGGED FOR REVIEW]" in notes_after_flag
        assert "[REVIEW] Approved" in notes_after_approve
        assert len(notes_after_approve) > len(notes_after_flag)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
