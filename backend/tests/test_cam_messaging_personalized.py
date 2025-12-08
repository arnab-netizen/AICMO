"""
Tests for CAM-AUTO personalized messaging (strategy-powered).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB
from aicmo.cam.domain import Channel, LeadSource, LeadStatus
from aicmo.cam.messaging import (
    SequenceConfig,
    generate_personalized_messages_for_lead,
    _extract_angle_from_strategy,
)
from aicmo.domain.strategy import StrategyDoc


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing (CAM tables only)."""
    engine = create_engine("sqlite:///:memory:")
    
    # Create only CAM tables explicitly
    CampaignDB.__table__.create(engine)
    LeadDB.__table__.create(engine)
    OutreachAttemptDB.__table__.create(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_campaign(in_memory_db):
    """Create a sample campaign."""
    campaign = CampaignDB(
        name="Test Campaign",
        description="Automated content marketing for SMBs",
        target_niche="SaaS",
        active=True,
    )
    in_memory_db.add(campaign)
    in_memory_db.commit()
    in_memory_db.refresh(campaign)
    return campaign


@pytest.fixture
def sample_lead(in_memory_db, sample_campaign):
    """Create a sample lead."""
    lead = LeadDB(
        campaign_id=sample_campaign.id,
        name="Jane Doe",
        company="TechCorp",
        role="CMO",
        email="jane@techcorp.com",
        linkedin_url="https://linkedin.com/in/janedoe",
        source=LeadSource.CSV,
        status=LeadStatus.NEW,
        notes="High-value prospect",
    )
    in_memory_db.add(lead)
    in_memory_db.commit()
    in_memory_db.refresh(lead)
    return lead


@pytest.fixture
def fake_strategy_doc():
    """Create a fake StrategyDoc for testing."""
    return StrategyDoc(
        brand_name="AICMO",
        executive_summary="Transform chaotic marketing into predictable growth",
        situation_analysis="Target SMBs struggling with inconsistent marketing",
        strategy_narrative="Focus on automation and systemization",
        primary_goal="Transform chaotic marketing into a predictable growth engine with content automation",
    )


def test_extract_angle_from_strategy_with_valid_doc(fake_strategy_doc):
    """Test angle extraction from a valid StrategyDoc."""
    angle = _extract_angle_from_strategy(fake_strategy_doc)
    
    assert "Transform chaotic marketing" in angle
    assert "predictable" in angle


def test_extract_angle_from_strategy_with_empty_payload():
    """Test angle extraction with empty payload falls back gracefully."""
    empty_doc = StrategyDoc(
        brand_name="Test",
        executive_summary="Test",
        situation_analysis="Test",
        strategy_narrative="Brief strategy narrative for testing fallback behavior",
    )
    angle = _extract_angle_from_strategy(empty_doc)
    
    # Should use strategy_narrative as fallback
    assert "Brief strategy" in angle or "chaotic" in angle.lower()


def test_extract_angle_from_strategy_with_none():
    """Test angle extraction with None returns fallback."""
    angle = _extract_angle_from_strategy(None)
    
    assert "chaotic" in angle.lower()
    assert "marketing" in angle.lower()


def test_generate_personalized_messages_for_lead_email(
    in_memory_db, sample_lead, fake_strategy_doc
):
    """Test personalized message generation for email channel."""
    sequence = SequenceConfig(channel=Channel.EMAIL, steps=3)
    
    messages = generate_personalized_messages_for_lead(
        db=in_memory_db,
        lead_id=sample_lead.id,
        channel=Channel.EMAIL,
        sequence=sequence,
        strategy_doc=fake_strategy_doc,
    )
    
    assert len(messages) == 3
    
    # Check first message
    msg1 = messages[0]
    assert msg1.step_number == 1
    assert msg1.channel == Channel.EMAIL
    assert msg1.subject is not None
    assert "Jane" in msg1.subject  # First name
    assert "TechCorp" in msg1.subject or "brand" in msg1.subject
    
    # Check body contains personalization
    assert "Hi Jane" in msg1.body
    assert "TechCorp" in msg1.body
    assert "SaaS" in msg1.body  # From campaign.target_niche
    assert "Transform chaotic marketing" in msg1.body  # From strategy
    
    # Check step 1 CTA
    assert "15-min chat" in msg1.body or "growth plans" in msg1.body
    
    # Check second message
    msg2 = messages[1]
    assert msg2.step_number == 2
    assert "following up" in msg2.body or "slipped past" in msg2.body
    
    # Check third message
    msg3 = messages[2]
    assert msg3.step_number == 3
    assert "not the right time" in msg3.body or "close the loop" in msg3.body


def test_generate_personalized_messages_for_lead_linkedin(
    in_memory_db, sample_lead, fake_strategy_doc
):
    """Test personalized message generation for LinkedIn channel."""
    sequence = SequenceConfig(channel=Channel.LINKEDIN, steps=2)
    
    messages = generate_personalized_messages_for_lead(
        db=in_memory_db,
        lead_id=sample_lead.id,
        channel=Channel.LINKEDIN,
        sequence=sequence,
        strategy_doc=fake_strategy_doc,
    )
    
    assert len(messages) == 2
    
    # LinkedIn messages should have no subject
    msg1 = messages[0]
    assert msg1.subject is None
    assert msg1.channel == Channel.LINKEDIN
    assert "Hi Jane" in msg1.body


def test_generate_personalized_messages_lead_not_found(in_memory_db, fake_strategy_doc):
    """Test error handling when lead doesn't exist."""
    sequence = SequenceConfig(channel=Channel.EMAIL, steps=1)
    
    with pytest.raises(ValueError, match="Lead 99999 not found"):
        generate_personalized_messages_for_lead(
            db=in_memory_db,
            lead_id=99999,
            channel=Channel.EMAIL,
            sequence=sequence,
            strategy_doc=fake_strategy_doc,
        )


def test_generate_personalized_messages_no_campaign(in_memory_db, fake_strategy_doc):
    """Test error handling when lead has no campaign."""
    lead = LeadDB(
        campaign_id=None,
        name="Orphan Lead",
        company="NoCampaign Inc",
        role="CEO",
        email="orphan@nocampaign.com",
        source=LeadSource.CSV,
        status=LeadStatus.NEW,
    )
    in_memory_db.add(lead)
    in_memory_db.commit()
    in_memory_db.refresh(lead)
    
    sequence = SequenceConfig(channel=Channel.EMAIL, steps=1)
    
    with pytest.raises(ValueError, match="has no campaign_id"):
        generate_personalized_messages_for_lead(
            db=in_memory_db,
            lead_id=lead.id,
            channel=Channel.EMAIL,
            sequence=sequence,
            strategy_doc=fake_strategy_doc,
        )
