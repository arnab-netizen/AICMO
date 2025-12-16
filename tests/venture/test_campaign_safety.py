"""
Tests for Module 0: Venture & Campaign Configuration.

Verifies:
- Campaign safety enforcement
- Kill switch functionality
- Status-based execution control
"""

import pytest
from sqlalchemy.orm import Session

from aicmo.venture.models import VentureDB, CampaignConfigDB, CampaignStatus
from aicmo.venture.enforcement import enforce_campaign_safety, can_send_message, SafetyViolation
from aicmo.cam.db_models import CampaignDB
from backend.db.session import get_session


@pytest.fixture
def venture(db_session: Session):
    """Create a test venture."""
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
    """Create a test campaign."""
    campaign = CampaignDB(
        name="test-campaign",
        description="Test campaign",
        active=True
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest.fixture
def campaign_config(db_session: Session, venture, campaign):
    """Create a campaign config."""
    config = CampaignConfigDB(
        campaign_id=campaign.id,
        venture_id=venture.id,
        objective="Test objective",
        status=CampaignStatus.DRAFT,
        kill_switch=False
    )
    db_session.add(config)
    db_session.commit()
    return config


def test_campaign_blocked_when_not_running(db_session: Session, campaign_config):
    """Campaign cannot send if status is not RUNNING."""
    # DRAFT status should block
    with pytest.raises(SafetyViolation, match="must be RUNNING"):
        enforce_campaign_safety(db_session, campaign_config.campaign_id)
    
    assert not can_send_message(db_session, campaign_config.campaign_id)


def test_campaign_allowed_when_running(db_session: Session, campaign_config):
    """Campaign can send when status is RUNNING and kill_switch is False."""
    # Set to RUNNING
    campaign_config.status = CampaignStatus.RUNNING
    db_session.commit()
    
    # Should not raise
    config = enforce_campaign_safety(db_session, campaign_config.campaign_id)
    assert config.campaign_id == campaign_config.campaign_id
    
    assert can_send_message(db_session, campaign_config.campaign_id)


def test_kill_switch_blocks_execution(db_session: Session, campaign_config):
    """Kill switch blocks execution even when RUNNING."""
    # Set to RUNNING but activate kill switch
    campaign_config.status = CampaignStatus.RUNNING
    campaign_config.kill_switch = True
    db_session.commit()
    
    with pytest.raises(SafetyViolation, match="kill switch is ACTIVE"):
        enforce_campaign_safety(db_session, campaign_config.campaign_id)
    
    assert not can_send_message(db_session, campaign_config.campaign_id)


def test_paused_campaign_blocked(db_session: Session, campaign_config):
    """PAUSED campaign cannot send messages."""
    campaign_config.status = CampaignStatus.PAUSED
    db_session.commit()
    
    with pytest.raises(SafetyViolation, match="is PAUSED"):
        enforce_campaign_safety(db_session, campaign_config.campaign_id)


def test_stopped_campaign_blocked(db_session: Session, campaign_config):
    """STOPPED campaign cannot send messages."""
    campaign_config.status = CampaignStatus.STOPPED
    db_session.commit()
    
    with pytest.raises(SafetyViolation, match="is STOPPED"):
        enforce_campaign_safety(db_session, campaign_config.campaign_id)


def test_missing_config_blocked(db_session: Session):
    """Campaign with no config cannot send."""
    with pytest.raises(SafetyViolation, match="has no configuration"):
        enforce_campaign_safety(db_session, 99999)  # Non-existent campaign
