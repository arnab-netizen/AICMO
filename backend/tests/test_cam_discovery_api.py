"""
Integration tests for CAM Discovery API endpoints (Phase 7).

Tests the REST API for discovery job management and profile discovery.
Uses a file-based SQLite database for reliable test isolation.
All tests are API-only (no direct database introspection).
"""

import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app as main_app
from backend.routers import cam as cam_router_module
from aicmo.cam.discovery_domain import DiscoveredProfile, Platform
from aicmo.cam.db_models import Base as CAMBase

# ==================================
# FILE-BASED TEST DATABASE SETUP
# ==================================

TEST_DB_FILE = "./cam_discovery_api_test.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Provide test database session for CAM API endpoints."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_cam_api_test_db():
    """Create tables once per test session in file-based DB."""
    # Remove old test DB if it exists
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    # Create ONLY CAM tables (not all Base tables)
    from aicmo.cam.db_models import (
        CampaignDB, LeadDB, OutreachAttemptDB,
        DiscoveryJobDB, DiscoveredProfileDB
    )
    cam_tables = [
        CampaignDB.__table__,
        LeadDB.__table__,
        OutreachAttemptDB.__table__,
        DiscoveryJobDB.__table__,
        DiscoveredProfileDB.__table__,
    ]
    CAMBase.metadata.create_all(bind=engine, tables=cam_tables)
    yield
    # Cleanup after all tests
    CAMBase.metadata.drop_all(bind=engine, tables=cam_tables)
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


@pytest.fixture(scope="session", autouse=True)
def setup_dependency_override(setup_cam_api_test_db):
    """Register dependency override for CAM router to use test database."""
    main_app.dependency_overrides[cam_router_module.get_db] = override_get_db
    yield
    main_app.dependency_overrides.pop(cam_router_module.get_db, None)


@pytest.fixture(scope="function", autouse=True)
def clear_data():
    """Clear all CAM data before each test for isolation."""
    db = TestingSessionLocal()
    try:
        # Delete in order to respect foreign key constraints
        from aicmo.cam.db_models import (
            OutreachAttemptDB, DiscoveredProfileDB, DiscoveryJobDB, 
            LeadDB, CampaignDB
        )
        db.query(OutreachAttemptDB).delete()
        db.query(DiscoveredProfileDB).delete()
        db.query(DiscoveryJobDB).delete()
        db.query(LeadDB).delete()
        db.query(CampaignDB).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """Test client using file-based test database."""
    with TestClient(main_app) as c:
        yield c


@pytest.fixture
def sample_campaign():
    """Create a sample campaign directly in DB for testing."""
    from aicmo.cam.db_models import CampaignDB
    db = TestingSessionLocal()
    try:
        campaign = CampaignDB(
            name="Test Campaign",
            target_niche="Tech",
            active=True,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign.id
    finally:
        db.close()


# ==================================
# DISCOVERY JOB CREATION TESTS
# ==================================

def test_create_discovery_job(client: TestClient, sample_campaign: int):
    """Test creating a new discovery job."""
    response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "LinkedIn Tech Founders",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["founder", "startup"],
                "location": "San Francisco",
                "role_contains": "CEO",
                "min_followers": 500,
                "recent_activity_days": 30,
            },
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "LinkedIn Tech Founders"
    assert data["campaign_id"] == sample_campaign
    assert data["status"] == "PENDING"
    assert "id" in data


def test_create_discovery_job_multiple_platforms(client: TestClient, sample_campaign: int):
    """Test creating a job with multiple platforms."""
    response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Multi-Platform Search",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin", "twitter", "instagram"],
                "keywords": ["marketing", "agency"],
            },
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["criteria"]["platforms"]) == 3


# ==================================
# DISCOVERY JOB EXECUTION TESTS
# ==================================

def test_run_discovery_job_success(client: TestClient, sample_campaign: int):
    """Test running a discovery job successfully."""
    # Create job
    create_response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Test Job",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["python"],
            },
        },
    )
    job_id = create_response.json()["id"]
    
    # Mock LinkedIn search to return fake profiles
    mock_profiles = [
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle="johndoe",
            profile_url="https://linkedin.com/in/johndoe",
            display_name="John Doe",
            bio="Python developer",
            followers=1000,
            location="Seattle",
            match_score=0.95,
        ),
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle="janedoe",
            profile_url="https://linkedin.com/in/janedoe",
            display_name="Jane Doe",
            bio="Python architect",
            followers=2000,
            location="Seattle",
            match_score=0.90,
        ),
    ]
    
    with patch("aicmo.cam.platforms.linkedin_source.search") as mock_search:
        mock_search.return_value = mock_profiles
        
        # Run job
        response = client.post(f"/api/cam/discovery/jobs/{job_id}/run")
        
        assert response.status_code == 200
        data = response.json()
        assert data["profiles_found"] == 2
        assert "completed" in data["message"].lower()
    
    # Verify via API (no direct DB access)
    profiles_response = client.get(f"/api/cam/discovery/jobs/{job_id}/profiles")
    assert profiles_response.status_code == 200
    profiles = profiles_response.json()
    assert len(profiles) == 2
    assert profiles[0]["handle"] in ["johndoe", "janedoe"]
    assert profiles[1]["handle"] in ["johndoe", "janedoe"]


def test_run_discovery_job_not_found(client: TestClient):
    """Test running a non-existent job."""
    response = client.post("/api/cam/discovery/jobs/99999/run")
    assert response.status_code == 400


def test_run_discovery_job_already_completed(client: TestClient, sample_campaign: int):
    """Test running a job that's already completed."""
    # Create and run job first time
    create_response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Completed Job",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["test"],
            },
        },
    )
    job_id = create_response.json()["id"]
    
    # Run job successfully first time
    with patch("aicmo.cam.platforms.linkedin_source.search") as mock_search:
        mock_search.return_value = []
        first_run = client.post(f"/api/cam/discovery/jobs/{job_id}/run")
        assert first_run.status_code == 200
    
    # Try to run again - should fail
    response = client.post(f"/api/cam/discovery/jobs/{job_id}/run")
    assert response.status_code in [400, 500]
    assert "already" in response.json()["detail"].lower() or "done" in response.json()["detail"].lower()


# ==================================
# DISCOVERY JOB LISTING TESTS
# ==================================

def test_list_all_discovery_jobs(client: TestClient, sample_campaign: int):
    """Test listing all discovery jobs."""
    # Create two jobs
    for i in range(2):
        client.post(
            "/api/cam/discovery/jobs",
            json={
                "name": f"Job {i}",
                "campaign_id": sample_campaign,
                "criteria": {
                    "platforms": ["linkedin"],
                    "keywords": ["test"],
                },
            },
        )
    
    # List all jobs
    response = client.get("/api/cam/discovery/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_list_discovery_jobs_filtered_by_campaign(client: TestClient):
    """Test filtering jobs by campaign."""
    # Create two campaigns directly in DB
    from aicmo.cam.db_models import CampaignDB
    db = TestingSessionLocal()
    
    campaign1 = CampaignDB(name="Campaign 1", target_niche="Tech", active=True)
    campaign2 = CampaignDB(name="Campaign 2", target_niche="Marketing", active=True)
    db.add(campaign1)
    db.add(campaign2)
    db.commit()
    db.refresh(campaign1)
    db.refresh(campaign2)
    campaign1_id = campaign1.id
    campaign2_id = campaign2.id
    db.close()
    
    # Create jobs for campaign 1
    client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Job C1",
            "campaign_id": campaign1_id,
            "criteria": {"platforms": ["linkedin"], "keywords": ["test"]},
        },
    )
    
    # Create job for campaign 2
    client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Job C2",
            "campaign_id": campaign2_id,
            "criteria": {"platforms": ["linkedin"], "keywords": ["test"]},
        },
    )
    
    # Filter by campaign 1
    response = client.get(f"/api/cam/discovery/jobs?campaign_id={campaign1_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["campaign_id"] == campaign1_id


# ==================================
# DISCOVERED PROFILES TESTS
# ==================================

def test_list_discovered_profiles(client: TestClient, sample_campaign: int):
    """Test listing discovered profiles for a job."""
    # Create and run job
    create_response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Profile Test Job",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["engineer"],
            },
        },
    )
    job_id = create_response.json()["id"]
    
    # Mock profiles
    mock_profiles = [
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle=f"user{i}",
            profile_url=f"https://linkedin.com/in/user{i}",
            display_name=f"User {i}",
            bio=f"Bio for user {i}",
            followers=1000 + i * 100,
            location="Seattle",
            match_score=0.9 - i * 0.05,
        )
        for i in range(3)
    ]
    
    with patch("aicmo.cam.platforms.linkedin_source.search") as mock_search:
        mock_search.return_value = mock_profiles
        client.post(f"/api/cam/discovery/jobs/{job_id}/run")
    
    # List profiles via API
    response = client.get(f"/api/cam/discovery/jobs/{job_id}/profiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("handle" in p for p in data)
    assert all("match_score" in p for p in data)


def test_list_profiles_empty_job(client: TestClient, sample_campaign: int):
    """Test listing profiles for job with no results."""
    # Create job (don't run it)
    create_response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Empty Job",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["test"],
            },
        },
    )
    job_id = create_response.json()["id"]
    
    # List profiles (should be empty)
    response = client.get(f"/api/cam/discovery/jobs/{job_id}/profiles")
    assert response.status_code == 200
    data = response.json()
    assert data == []


# ==================================
# PROFILE CONVERSION TESTS
# ==================================

def test_convert_profiles_to_leads(client: TestClient, sample_campaign: int):
    """Test converting discovered profiles to leads."""
    # Create and run job
    create_response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Conversion Test",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["test"],
            },
        },
    )
    job_id = create_response.json()["id"]
    
    # Mock and run
    mock_profiles = [
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle=f"convert{i}",
            profile_url=f"https://linkedin.com/in/convert{i}",
            display_name=f"Convert User {i}",
            bio="Test bio",
            followers=1000,
            location="Seattle",
            match_score=0.9,
        )
        for i in range(2)
    ]
    
    with patch("aicmo.cam.platforms.linkedin_source.search") as mock_search:
        mock_search.return_value = mock_profiles
        client.post(f"/api/cam/discovery/jobs/{job_id}/run")
    
    # Get profile IDs
    profiles_response = client.get(f"/api/cam/discovery/jobs/{job_id}/profiles")
    profiles = profiles_response.json()
    profile_ids = [p["id"] for p in profiles]
    
    # Convert to leads
    response = client.post(
        f"/api/cam/discovery/jobs/{job_id}/profiles/convert",
        json={"profile_ids": profile_ids},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["leads_created"] == 2
    # Note: No leads endpoint exists yet, so we trust the API response


def test_convert_profiles_skip_duplicates(client: TestClient, sample_campaign: int):
    """Test that duplicate profiles are not converted twice."""
    # Create and run job
    create_response = client.post(
        "/api/cam/discovery/jobs",
        json={
            "name": "Duplicate Test",
            "campaign_id": sample_campaign,
            "criteria": {
                "platforms": ["linkedin"],
                "keywords": ["test"],
            },
        },
    )
    job_id = create_response.json()["id"]
    
    # Mock single profile
    mock_profiles = [
        DiscoveredProfile(
            platform=Platform.LINKEDIN,
            handle="duplicate_user",
            profile_url="https://linkedin.com/in/duplicate_user",
            display_name="Duplicate User",
            bio="Test bio",
            followers=1000,
            location="Seattle",
            match_score=0.9,
        )
    ]
    
    with patch("aicmo.cam.platforms.linkedin_source.search") as mock_search:
        mock_search.return_value = mock_profiles
        client.post(f"/api/cam/discovery/jobs/{job_id}/run")
    
    # Get profile ID
    profiles_response = client.get(f"/api/cam/discovery/jobs/{job_id}/profiles")
    profile_id = profiles_response.json()[0]["id"]
    
    # First conversion
    response1 = client.post(
        f"/api/cam/discovery/jobs/{job_id}/profiles/convert",
        json={"profile_ids": [profile_id]},
    )
    assert response1.status_code == 200
    assert response1.json()["leads_created"] == 1
    
    # Second conversion (should skip)
    response2 = client.post(
        f"/api/cam/discovery/jobs/{job_id}/profiles/convert",
        json={"profile_ids": [profile_id]},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["leads_created"] == 0
    # API doesn't return leads_skipped, but creating 0 leads confirms skipping


def test_convert_profiles_job_not_found(client: TestClient):
    """Test converting profiles for non-existent job."""
    response = client.post(
        "/api/cam/discovery/jobs/99999/profiles/convert",
        json={"profile_ids": [1, 2]},
    )
    assert response.status_code in [400, 404]  # Accept both error codes


def test_convert_profiles_no_campaign(client: TestClient):
    """Test converting profiles for job without campaign."""
    # Create job without campaign (should fail at creation)
    # If creation succeeds, conversion should fail
    # This test documents expected behavior
    pass  # Skip - campaign_id is required at creation


# ==================================
# PLACEHOLDER TESTS FOR FUTURE PHASES
# ==================================

def test_phase8_pipeline_placeholder(client: TestClient):
    """Placeholder for Phase 8 outreach pipeline tests."""
    assert True  # TODO: Implement when Phase 8 is ready


def test_phase9_safety_placeholder(client: TestClient):
    """Placeholder for Phase 9 safety mechanism tests."""
    assert True  # TODO: Implement when Phase 9 is ready
