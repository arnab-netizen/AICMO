"""
Tests for CAM Phase 7 Discovery Service.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.cam.db_models import (
    CampaignDB,
    LeadDB,
    DiscoveryJobDB,
    DiscoveredProfileDB,
)
from aicmo.cam.discovery_domain import (
    DiscoveryCriteria,
    DiscoveredProfile,
    Platform,
)
from aicmo.cam.discovery import (
    create_discovery_job,
    run_discovery_job,
    convert_profiles_to_leads,
    list_discovery_jobs,
    list_discovered_profiles,
)


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite DB with CAM tables."""
    engine = create_engine("sqlite:///:memory:")
    
    CampaignDB.__table__.create(engine)
    LeadDB.__table__.create(engine)
    DiscoveryJobDB.__table__.create(engine)
    DiscoveredProfileDB.__table__.create(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_campaign(in_memory_db):
    """Create sample campaign."""
    campaign = CampaignDB(
        name="Discovery Test Campaign",
        description="Test",
        active=True,
    )
    in_memory_db.add(campaign)
    in_memory_db.commit()
    in_memory_db.refresh(campaign)
    return campaign


@pytest.fixture
def mock_linkedin_profiles():
    """Mock LinkedIn search results."""
    return [
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle="jane-cmo",
            profile_url="https://linkedin.com/in/jane-cmo",
            display_name="Jane Smith",
            bio="CMO at TechCorp, passionate about growth",
            followers=2500,
            location="San Francisco, CA",
            match_score=0.9,
        ),
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle="john-marketing",
            profile_url="https://linkedin.com/in/john-marketing",
            display_name="John Doe",
            bio="Marketing Director at StartupCo",
            followers=1200,
            location="Austin, TX",
            match_score=0.75,
        ),
    ]


def test_create_discovery_job(in_memory_db, sample_campaign):
    """Test creating a discovery job."""
    criteria = DiscoveryCriteria(
        platforms=[Platform.LINKEDIN],
        keywords=["CMO", "marketing"],
        location="San Francisco",
        role_contains="Chief",
    )
    
    job = create_discovery_job(
        db=in_memory_db,
        campaign_id=sample_campaign.id,
        name="Test Job",
        criteria=criteria,
    )
    
    assert job.id is not None
    assert job.name == "Test Job"
    assert job.status == "PENDING"
    assert job.campaign_id == sample_campaign.id
    assert "linkedin" in job.criteria["platforms"]


@patch("aicmo.cam.discovery.linkedin_source.search")
def test_run_discovery_job_success(mock_search, in_memory_db, sample_campaign, mock_linkedin_profiles):
    """Test successful discovery job execution."""
    mock_search.return_value = mock_linkedin_profiles
    
    criteria = DiscoveryCriteria(
        platforms=[Platform.LINKEDIN],
        keywords=["CMO"],
    )
    
    job = create_discovery_job(
        db=in_memory_db,
        campaign_id=sample_campaign.id,
        name="LinkedIn CMO Search",
        criteria=criteria,
    )
    
    profiles = run_discovery_job(db=in_memory_db, job_id=job.id)
    
    # Verify job status updated
    in_memory_db.refresh(job)
    assert job.status == "DONE"
    assert job.completed_at is not None
    
    # Verify profiles returned
    assert len(profiles) == 2
    assert profiles[0].handle == "jane-cmo"
    
    # Verify profiles persisted to DB
    profile_dbs = list_discovered_profiles(db=in_memory_db, job_id=job.id)
    assert len(profile_dbs) == 2


@patch("aicmo.cam.discovery.linkedin_source.search")
@patch("aicmo.cam.discovery.twitter_source.search")
def test_run_discovery_job_multiple_platforms(
    mock_twitter, mock_linkedin, in_memory_db, sample_campaign
):
    """Test discovery across multiple platforms."""
    mock_linkedin.return_value = [
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle="linkedin-user",
            profile_url="https://linkedin.com/in/linkedin-user",
            display_name="LinkedIn User",
            match_score=0.8,
        ),
    ]
    
    mock_twitter.return_value = [
        DiscoveredProfile(
            platform=Platform.TWITTER,
            handle="twitter_user",
            profile_url="https://twitter.com/twitter_user",
            display_name="Twitter User",
            match_score=0.7,
        ),
    ]
    
    criteria = DiscoveryCriteria(
        platforms=[Platform.LINKEDIN, Platform.TWITTER],
        keywords=["tech"],
    )
    
    job = create_discovery_job(
        db=in_memory_db,
        campaign_id=sample_campaign.id,
        name="Multi-Platform Search",
        criteria=criteria,
    )
    
    profiles = run_discovery_job(db=in_memory_db, job_id=job.id)
    
    assert len(profiles) == 2
    platforms = {p.platform for p in profiles}
    assert Platform.LINKEDIN in platforms
    assert Platform.TWITTER in platforms


def test_convert_profiles_to_leads(in_memory_db, sample_campaign):
    """Test converting discovered profiles to leads."""
    # Create discovery job
    job = DiscoveryJobDB(
        name="Conversion Test",
        criteria={"platforms": ["linkedin"]},
        campaign_id=sample_campaign.id,
        status="DONE",
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    # Add discovered profiles
    profile1 = DiscoveredProfileDB(
        job_id=job.id,
        platform="linkedin",
        handle="convert-test-1",
        profile_url="https://linkedin.com/in/convert-test-1",
        display_name="Convert Test 1",
        bio="VP of Marketing",
        match_score=0.9,
    )
    profile2 = DiscoveredProfileDB(
        job_id=job.id,
        platform="linkedin",
        handle="convert-test-2",
        profile_url="https://linkedin.com/in/convert-test-2",
        display_name="Convert Test 2",
        bio="CMO",
        match_score=0.85,
    )
    in_memory_db.add_all([profile1, profile2])
    in_memory_db.commit()
    in_memory_db.refresh(profile1)
    in_memory_db.refresh(profile2)
    
    # Convert to leads
    created_count = convert_profiles_to_leads(
        db=in_memory_db,
        profile_ids=[profile1.id, profile2.id],
        campaign_id=sample_campaign.id,
    )
    
    assert created_count == 2
    
    # Verify leads created
    leads = in_memory_db.query(LeadDB).filter(LeadDB.campaign_id == sample_campaign.id).all()
    assert len(leads) == 2
    assert leads[0].name in ["Convert Test 1", "Convert Test 2"]


def test_convert_profiles_skip_duplicates(in_memory_db, sample_campaign):
    """Test that duplicate profiles are skipped during conversion."""
    # Create job and profile
    job = DiscoveryJobDB(
        name="Duplicate Test",
        criteria={"platforms": ["linkedin"]},
        campaign_id=sample_campaign.id,
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    profile = DiscoveredProfileDB(
        job_id=job.id,
        platform="linkedin",
        handle="duplicate-user",
        profile_url="https://linkedin.com/in/duplicate-user",
        display_name="Duplicate User",
        match_score=0.8,
    )
    in_memory_db.add(profile)
    in_memory_db.commit()
    in_memory_db.refresh(profile)
    
    # First conversion
    count1 = convert_profiles_to_leads(
        db=in_memory_db,
        profile_ids=[profile.id],
        campaign_id=sample_campaign.id,
    )
    assert count1 == 1
    
    # Second conversion (should skip duplicate)
    count2 = convert_profiles_to_leads(
        db=in_memory_db,
        profile_ids=[profile.id],
        campaign_id=sample_campaign.id,
    )
    assert count2 == 0
    
    # Verify only 1 lead exists
    leads = in_memory_db.query(LeadDB).filter(LeadDB.campaign_id == sample_campaign.id).all()
    assert len(leads) == 1


def test_list_discovery_jobs(in_memory_db, sample_campaign):
    """Test listing discovery jobs."""
    # Create multiple jobs
    for i in range(3):
        job = DiscoveryJobDB(
            name=f"Job {i}",
            criteria={"platforms": ["linkedin"]},
            campaign_id=sample_campaign.id,
        )
        in_memory_db.add(job)
    in_memory_db.commit()
    
    jobs = list_discovery_jobs(db=in_memory_db, campaign_id=sample_campaign.id)
    assert len(jobs) == 3


def test_list_discovered_profiles(in_memory_db, sample_campaign):
    """Test listing profiles for a job."""
    job = DiscoveryJobDB(
        name="Profile List Test",
        criteria={"platforms": ["twitter"]},
        campaign_id=sample_campaign.id,
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    # Add profiles
    for i in range(5):
        profile = DiscoveredProfileDB(
            job_id=job.id,
            platform="twitter",
            handle=f"user{i}",
            profile_url=f"https://twitter.com/user{i}",
            display_name=f"User {i}",
            match_score=0.5 + (i * 0.1),
        )
        in_memory_db.add(profile)
    in_memory_db.commit()
    
    profiles = list_discovered_profiles(db=in_memory_db, job_id=job.id)
    assert len(profiles) == 5
    # Should be ordered by match_score desc
    assert profiles[0].match_score >= profiles[-1].match_score
