"""
Tests for CAM Phase 7 Discovery DB models.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aicmo.cam.db_models import (
    Base,
    CampaignDB,
    DiscoveryJobDB,
    DiscoveredProfileDB,
)


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite DB with CAM tables."""
    engine = create_engine("sqlite:///:memory:")
    
    # Create all CAM tables
    CampaignDB.__table__.create(engine)
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
        name="Test Discovery Campaign",
        description="For testing discovery features",
        target_niche="SaaS",
        active=True,
    )
    in_memory_db.add(campaign)
    in_memory_db.commit()
    in_memory_db.refresh(campaign)
    return campaign


def test_create_discovery_job(in_memory_db, sample_campaign):
    """Test creating a discovery job."""
    job = DiscoveryJobDB(
        name="Test Job",
        criteria={"platforms": ["linkedin"], "keywords": ["CMO", "marketing"]},
        campaign_id=sample_campaign.id,
        status="PENDING",
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    assert job.id is not None
    assert job.name == "Test Job"
    assert job.status == "PENDING"
    assert job.campaign_id == sample_campaign.id
    assert "linkedin" in job.criteria["platforms"]


def test_create_discovered_profile(in_memory_db, sample_campaign):
    """Test creating a discovered profile."""
    # Create job first
    job = DiscoveryJobDB(
        name="Test Job",
        criteria={"platforms": ["linkedin"], "keywords": ["CEO"]},
        campaign_id=sample_campaign.id,
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    # Create profile
    profile = DiscoveredProfileDB(
        job_id=job.id,
        platform="linkedin",
        handle="johndoe",
        profile_url="https://linkedin.com/in/johndoe",
        display_name="John Doe",
        bio="CEO at TechCorp",
        followers=1500,
        location="San Francisco, CA",
        match_score=0.85,
    )
    in_memory_db.add(profile)
    in_memory_db.commit()
    in_memory_db.refresh(profile)
    
    assert profile.id is not None
    assert profile.job_id == job.id
    assert profile.platform == "linkedin"
    assert profile.handle == "johndoe"
    assert profile.match_score == 0.85


def test_discovery_job_status_transitions(in_memory_db, sample_campaign):
    """Test job status can be updated."""
    job = DiscoveryJobDB(
        name="Status Test Job",
        criteria={"platforms": ["twitter"]},
        campaign_id=sample_campaign.id,
        status="PENDING",
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    # Update to RUNNING
    job.status = "RUNNING"
    in_memory_db.commit()
    assert job.status == "RUNNING"
    
    # Update to DONE
    job.status = "DONE"
    in_memory_db.commit()
    assert job.status == "DONE"


def test_multiple_profiles_per_job(in_memory_db, sample_campaign):
    """Test multiple profiles can belong to one job."""
    job = DiscoveryJobDB(
        name="Multi-Profile Job",
        criteria={"platforms": ["instagram"]},
        campaign_id=sample_campaign.id,
    )
    in_memory_db.add(job)
    in_memory_db.commit()
    in_memory_db.refresh(job)
    
    # Add 3 profiles
    for i in range(3):
        profile = DiscoveredProfileDB(
            job_id=job.id,
            platform="instagram",
            handle=f"user{i}",
            profile_url=f"https://instagram.com/user{i}",
            display_name=f"User {i}",
            match_score=0.5 + (i * 0.1),
        )
        in_memory_db.add(profile)
    
    in_memory_db.commit()
    
    # Query profiles for this job
    profiles = (
        in_memory_db.query(DiscoveredProfileDB)
        .filter(DiscoveredProfileDB.job_id == job.id)
        .all()
    )
    
    assert len(profiles) == 3
    assert all(p.job_id == job.id for p in profiles)
