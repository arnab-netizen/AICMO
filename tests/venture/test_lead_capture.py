"""
Tests for MODULE 1: Lead Capture with Identity Resolution.

Verifies:
- Deduplication via identity_hash
- Consent status tracking
- DNC enforcement
- Attribution tracking
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from aicmo.venture.lead_capture import (
    capture_lead,
    generate_identity_hash,
    mark_lead_dnc,
    is_contactable,
    LeadCaptureRequest
)
from aicmo.venture.models import VentureDB
from aicmo.cam.db_models import CampaignDB, LeadDB


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
    return campaign


def test_identity_hash_same_for_same_email(db_session: Session):
    """Same email generates same identity hash."""
    hash1 = generate_identity_hash("test@example.com", None, None)
    hash2 = generate_identity_hash("test@example.com", None, None)
    assert hash1 == hash2


def test_identity_hash_different_for_different_email(db_session: Session):
    """Different emails generate different hashes."""
    hash1 = generate_identity_hash("test1@example.com", None, None)
    hash2 = generate_identity_hash("test2@example.com", None, None)
    assert hash1 != hash2


def test_deduplication_prevents_duplicate_leads(db_session: Session, venture, campaign):
    """Capturing same lead twice updates existing, doesn't create duplicate."""
    request = LeadCaptureRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        name="John Doe",
        email="john@example.com",
        consent_status="CONSENTED"
    )
    
    # First capture
    lead1 = capture_lead(db_session, request)
    lead1_id = lead1.id
    
    # Second capture with same email
    lead2 = capture_lead(db_session, request)
    
    # Should return same lead (updated)
    assert lead2.id == lead1_id
    
    # Should only have 1 lead in DB
    total_leads = db_session.query(LeadDB).filter_by(
        venture_id=venture.id,
        email="john@example.com"
    ).count()
    assert total_leads == 1


def test_touch_timestamps_updated_on_recapture(db_session: Session, venture, campaign):
    """Re-capturing lead updates last_touch_at."""
    request = LeadCaptureRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        name="Jane Doe",
        email="jane@example.com"
    )
    
    # First capture
    lead1 = capture_lead(db_session, request)
    first_touch = lead1.first_touch_at
    last_touch_1 = lead1.last_touch_at
    
    # Wait a moment, then re-capture
    import time
    time.sleep(0.1)
    
    lead2 = capture_lead(db_session, request)
    
    # first_touch should remain the same
    assert lead2.first_touch_at == first_touch
    
    # last_touch should be updated
    assert lead2.last_touch_at > last_touch_1


def test_consent_status_tracked(db_session: Session, venture, campaign):
    """Consent status is persisted."""
    request = LeadCaptureRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        name="Consenting User",
        email="consent@example.com",
        consent_status="CONSENTED"
    )
    
    lead = capture_lead(db_session, request)
    
    assert lead.consent_status == "CONSENTED"
    assert lead.consent_date is not None


def test_dnc_marking_blocks_contact(db_session: Session, venture, campaign):
    """Marking lead as DNC prevents contact."""
    request = LeadCaptureRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        name="DNC User",
        email="dnc@example.com",
        consent_status="CONSENTED"
    )
    
    lead = capture_lead(db_session, request)
    
    # Initially contactable
    assert is_contactable(db_session, lead.id)
    
    # Mark as DNC
    mark_lead_dnc(db_session, lead.id)
    
    # Now not contactable
    assert not is_contactable(db_session, lead.id)
    
    # Verify status updated in DB
    db_session.refresh(lead)
    assert lead.consent_status == "DNC"


def test_attribution_data_captured(db_session: Session, venture, campaign):
    """Attribution data (UTM params, source) is persisted."""
    request = LeadCaptureRequest(
        venture_id=venture.id,
        campaign_id=campaign.id,
        name="Attributed User",
        email="attr@example.com",
        source_channel="linkedin",
        source_ref="ad_campaign_123",
        utm_campaign="summer_launch",
        utm_content="video_ad"
    )
    
    lead = capture_lead(db_session, request)
    
    assert lead.source_channel == "linkedin"
    assert lead.source_ref == "ad_campaign_123"
    assert lead.utm_campaign == "summer_launch"
    assert lead.utm_content == "video_ad"


def test_nonexistent_lead_not_contactable(db_session: Session):
    """Nonexistent lead returns False for is_contactable."""
    assert not is_contactable(db_session, 99999)
