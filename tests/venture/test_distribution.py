"""
Tests for MODULE 2: Distribution Automation with Safety.

Verifies:
- DNC enforcement blocks distribution
- Campaign safety blocks distribution
- Kill switch blocks distribution
- Distribution tracking
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from aicmo.venture.distribution import (
    execute_distribution,
    can_distribute,
    get_distribution_count,
    DistributionRequest,
    DistributionBlocked
)
from aicmo.venture.models import VentureDB, CampaignConfigDB, CampaignStatus
from aicmo.venture.lead_capture import capture_lead, mark_lead_dnc, LeadCaptureRequest
from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.venture.distribution_models import DistributionJobDB


@pytest.fixture
def venture(db_session: Session):
    """Create test venture."""
    venture = VentureDB(
        id="test-venture",
        venture_name="Test Venture",
        offer_summary="Test product",
        primary_cta="Sign up",
        owner_contact="test@example.com"
    )
    db_session.add(venture)
    db_session.commit()
    return venture


@pytest.fixture
def campaign(db_session: Session, venture):
    """Create test campaign."""
    campaign = CampaignDB(
        name="test-campaign",
        description="Test campaign",
        active=True
    )
    db_session.add(campaign)
    db_session.commit()
    
    # Add config
    config = CampaignConfigDB(
        campaign_id=campaign.id,
        venture_id=venture.id,
        objective="Test objective",
        status=CampaignStatus.RUNNING,
        kill_switch=False
    )
    db_session.add(config)
    db_session.commit()
    
    return campaign


@pytest.fixture
def lead(db_session: Session, venture, campaign):
    """Create test lead."""
    request = LeadCaptureRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        name="Test Lead",
        email="test@example.com",
        consent_status="CONSENTED"
    )
    return capture_lead(db_session, request)


def test_dnc_lead_blocks_distribution(db_session: Session, venture, campaign, lead):
    """Lead with DNC status cannot receive messages."""
    # Mark lead as DNC
    mark_lead_dnc(db_session, lead.id)
    
    # Attempt distribution
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    with pytest.raises(DistributionBlocked, match="Do Not Contact"):
        execute_distribution(db_session, request)
    
    # Verify BLOCKED job was created
    job = db_session.query(DistributionJobDB).filter_by(lead_id=lead.id).first()
    assert job is not None
    assert job.status == "BLOCKED"
    assert "Do Not Contact" in job.error


def test_paused_campaign_blocks_distribution(db_session: Session, venture, campaign, lead):
    """Paused campaign cannot send messages."""
    # Pause campaign
    config = db_session.query(CampaignConfigDB).filter_by(campaign_id=campaign.id).first()
    config.status = CampaignStatus.PAUSED
    db_session.commit()
    
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    with pytest.raises(DistributionBlocked, match="PAUSED"):
        execute_distribution(db_session, request)


def test_kill_switch_blocks_distribution(db_session: Session, venture, campaign, lead):
    """Kill switch blocks all distribution."""
    # Activate kill switch
    config = db_session.query(CampaignConfigDB).filter_by(campaign_id=campaign.id).first()
    config.kill_switch = True
    db_session.commit()
    
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    with pytest.raises(DistributionBlocked, match="kill switch"):
        execute_distribution(db_session, request)


def test_successful_distribution_creates_job(db_session: Session, venture, campaign, lead):
    """Successful distribution creates job record."""
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    job = execute_distribution(db_session, request)
    
    assert job.status == "SENT"
    assert job.executed_at is not None
    assert job.message_id is not None
    assert job.channel == "email"


def test_dry_run_mode(db_session: Session, venture, campaign, lead):
    """Dry run performs checks but doesn't send."""
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    job = execute_distribution(db_session, request, dry_run=True)
    
    assert job.status == "DRY_RUN"
    assert job.executed_at is not None


def test_distribution_count_tracking(db_session: Session, venture, campaign, lead):
    """Distribution count tracks sent messages."""
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    # Send 3 messages
    for _ in range(3):
        execute_distribution(db_session, request)
    
    count = get_distribution_count(db_session, campaign.id)
    assert count == 3


def test_distribution_count_since_timestamp(db_session: Session, venture, campaign, lead):
    """Distribution count can be filtered by timestamp."""
    request = DistributionRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        lead_id=lead.id,
        channel="email",
        message_content="Test message"
    )
    
    # Send message
    execute_distribution(db_session, request)
    
    # Count since 1 hour ago (should include)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    count = get_distribution_count(db_session, campaign.id, since=one_hour_ago)
    assert count == 1
    
    # Count since 1 hour in future (should exclude)
    one_hour_future = datetime.now(timezone.utc) + timedelta(hours=1)
    count = get_distribution_count(db_session, campaign.id, since=one_hour_future)
    assert count == 0
