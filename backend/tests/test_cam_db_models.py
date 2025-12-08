"""
CAM database models tests.

Verifies CAM tables can be created and queried.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.core.db import Base
from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB
from aicmo.cam.domain import LeadSource, LeadStatus, Channel, AttemptStatus


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing CAM tables only."""
    engine = create_engine("sqlite:///:memory:")
    
    # Create only CAM tables, not all Base tables
    CampaignDB.__table__.create(engine, checkfirst=True)
    LeadDB.__table__.create(engine, checkfirst=True)
    OutreachAttemptDB.__table__.create(engine, checkfirst=True)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestCAMDatabaseModels:
    """Test CAM database models."""
    
    def test_create_campaign(self, db_session):
        """Test creating a campaign in the database."""
        campaign = CampaignDB(
            name="Test Campaign",
            description="Testing CAM",
            target_niche="SaaS founders",
            active=True,
        )
        db_session.add(campaign)
        db_session.commit()
        
        # Query it back
        result = db_session.query(CampaignDB).filter_by(name="Test Campaign").first()
        assert result is not None
        assert result.name == "Test Campaign"
        assert result.description == "Testing CAM"
        assert result.target_niche == "SaaS founders"
        assert result.active is True
    
    def test_create_lead(self, db_session):
        """Test creating a lead linked to a campaign."""
        # Create campaign first
        campaign = CampaignDB(name="Lead Test Campaign")
        db_session.add(campaign)
        db_session.commit()
        
        # Create lead
        lead = LeadDB(
            campaign_id=campaign.id,
            name="John Doe",
            company="Acme Corp",
            role="CEO",
            email="john@acme.com",
            linkedin_url="https://linkedin.com/in/johndoe",
            source=LeadSource.CSV,
            status=LeadStatus.NEW,
        )
        db_session.add(lead)
        db_session.commit()
        
        # Query it back
        result = db_session.query(LeadDB).filter_by(email="john@acme.com").first()
        assert result is not None
        assert result.name == "John Doe"
        assert result.company == "Acme Corp"
        assert result.role == "CEO"
        assert result.campaign_id == campaign.id
        assert result.source == LeadSource.CSV
        assert result.status == LeadStatus.NEW
    
    def test_create_outreach_attempt(self, db_session):
        """Test creating an outreach attempt."""
        # Create campaign and lead
        campaign = CampaignDB(name="Attempt Test Campaign")
        db_session.add(campaign)
        db_session.commit()
        
        lead = LeadDB(
            campaign_id=campaign.id,
            name="Jane Smith",
            email="jane@example.com",
        )
        db_session.add(lead)
        db_session.commit()
        
        # Create attempt
        attempt = OutreachAttemptDB(
            lead_id=lead.id,
            campaign_id=campaign.id,
            channel=Channel.LINKEDIN,
            step_number=1,
            status=AttemptStatus.PENDING,
        )
        db_session.add(attempt)
        db_session.commit()
        
        # Query it back
        result = db_session.query(OutreachAttemptDB).filter_by(lead_id=lead.id).first()
        assert result is not None
        assert result.campaign_id == campaign.id
        assert result.channel == Channel.LINKEDIN
        assert result.step_number == 1
        assert result.status == AttemptStatus.PENDING
    
    def test_campaign_unique_name_constraint(self, db_session):
        """Test that campaign names must be unique."""
        campaign1 = CampaignDB(name="Unique Campaign")
        db_session.add(campaign1)
        db_session.commit()
        
        # Try to create another with same name
        campaign2 = CampaignDB(name="Unique Campaign")
        db_session.add(campaign2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()
