"""
Tests for CAM Phase 9: Safety & Limits API.

Tests safety settings management, rate limiting, and compliance features.
Uses file-based SQLite database to avoid session isolation issues.
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import main app and db models
from backend.main import app as main_app
import backend.routers.cam as cam_router_module
from aicmo.cam.db_models import Base, CampaignDB, LeadDB, SafetySettingsDB


# ==========================================
# TEST DATABASE SETUP (File-Based)
# ==========================================

TEST_DB_FILE = "./cam_safety_api_test.db"
engine = create_engine(f"sqlite:///{TEST_DB_FILE}", echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Dependency override for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_cam_safety_api_test_db():
    """
    Setup test database once per test session.
    Creates only CAM tables, then drops them after all tests complete.
    """
    # Remove old test database if exists
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    # Create only CAM tables
    for table in [
        CampaignDB.__table__,
        LeadDB.__table__,
        SafetySettingsDB.__table__,
    ]:
        table.create(bind=engine, checkfirst=True)
    
    # Register dependency override
    main_app.dependency_overrides[cam_router_module.get_db] = override_get_db
    
    yield
    
    # Cleanup
    for table in [SafetySettingsDB.__table__, LeadDB.__table__, CampaignDB.__table__]:
        table.drop(bind=engine, checkfirst=True)
    
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    # Clear overrides
    main_app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def clear_data():
    """
    Clear all data before each test.
    Ensures test isolation by truncating tables.
    """
    db = TestingSessionLocal()
    try:
        db.execute(text("DELETE FROM cam_safety_settings"))
        db.execute(text("DELETE FROM cam_leads"))
        db.execute(text("DELETE FROM cam_campaigns"))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """Test client for API requests."""
    return TestClient(main_app)


# ==========================================
# TESTS: GET SAFETY SETTINGS
# ==========================================

def test_get_safety_default(client):
    """Test GET /api/cam/safety returns default settings."""
    response = client.get("/api/cam/safety")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify structure
    assert "per_channel_limits" in data
    assert "send_window_start" in data
    assert "send_window_end" in data
    assert "blocked_domains" in data
    assert "do_not_contact_emails" in data
    assert "do_not_contact_lead_ids" in data
    
    # Verify default values
    assert "email" in data["per_channel_limits"]
    assert data["per_channel_limits"]["email"]["max_per_day"] == 20
    assert data["per_channel_limits"]["email"]["warmup_enabled"] is True
    
    assert data["send_window_start"] == "09:00"
    assert data["send_window_end"] == "18:00"
    
    assert data["blocked_domains"] == []
    assert data["do_not_contact_emails"] == []
    assert data["do_not_contact_lead_ids"] == []


def test_get_safety_structure(client):
    """Test safety settings have correct structure."""
    response = client.get("/api/cam/safety")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check per_channel_limits structure
    for channel, config in data["per_channel_limits"].items():
        assert "channel" in config
        assert "max_per_day" in config
        assert "warmup_enabled" in config
        assert isinstance(config["max_per_day"], int)
        assert isinstance(config["warmup_enabled"], bool)


# ==========================================
# TESTS: UPDATE SAFETY SETTINGS
# ==========================================

def test_update_safety_settings(client):
    """Test PUT /api/cam/safety updates settings."""
    # Get initial settings
    initial_response = client.get("/api/cam/safety")
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    
    # Modify settings
    updated_data = initial_data.copy()
    updated_data["per_channel_limits"]["email"]["max_per_day"] = 50
    updated_data["send_window_start"] = "08:00"
    updated_data["send_window_end"] = "20:00"
    updated_data["blocked_domains"] = ["spam.com", "test.net"]
    updated_data["do_not_contact_emails"] = ["blocked@example.com"]
    
    # Update via API
    update_response = client.put("/api/cam/safety", json=updated_data)
    assert update_response.status_code == 200
    
    # Verify changes persisted
    verify_response = client.get("/api/cam/safety")
    assert verify_response.status_code == 200
    verified_data = verify_response.json()
    
    assert verified_data["per_channel_limits"]["email"]["max_per_day"] == 50
    assert verified_data["send_window_start"] == "08:00"
    assert verified_data["send_window_end"] == "20:00"
    assert verified_data["blocked_domains"] == ["spam.com", "test.net"]
    assert verified_data["do_not_contact_emails"] == ["blocked@example.com"]


def test_update_dnc_lead_ids(client):
    """Test updating do_not_contact_lead_ids list."""
    # Get initial settings
    response = client.get("/api/cam/safety")
    data = response.json()
    
    # Add lead IDs to DNC list
    data["do_not_contact_lead_ids"] = [1, 2, 3]
    
    # Update
    update_response = client.put("/api/cam/safety", json=data)
    assert update_response.status_code == 200
    
    # Verify
    verify_response = client.get("/api/cam/safety")
    verified_data = verify_response.json()
    assert verified_data["do_not_contact_lead_ids"] == [1, 2, 3]


def test_update_warmup_settings(client):
    """Test updating warmup configuration."""
    response = client.get("/api/cam/safety")
    data = response.json()
    
    # Modify warmup settings for linkedin
    data["per_channel_limits"]["linkedin"]["warmup_enabled"] = False
    data["per_channel_limits"]["linkedin"]["max_per_day"] = 25
    
    # Update
    update_response = client.put("/api/cam/safety", json=data)
    assert update_response.status_code == 200
    
    # Verify
    verify_response = client.get("/api/cam/safety")
    verified_data = verify_response.json()
    
    assert verified_data["per_channel_limits"]["linkedin"]["warmup_enabled"] is False
    assert verified_data["per_channel_limits"]["linkedin"]["max_per_day"] == 25


# ==========================================
# TESTS: SAFETY SETTINGS ROUNDTRIP
# ==========================================

def test_safety_roundtrip_structure(client):
    """Test complete roundtrip preserves all fields."""
    # Get settings
    get_response = client.get("/api/cam/safety")
    original_data = get_response.json()
    
    # Add data to all fields
    modified_data = {
        "per_channel_limits": {
            "email": {
                "channel": "email",
                "max_per_day": 100,
                "warmup_enabled": False,
                "warmup_start": None,
                "warmup_increment": None,
                "warmup_max": None,
            },
            "linkedin": {
                "channel": "linkedin",
                "max_per_day": 50,
                "warmup_enabled": True,
                "warmup_start": 10,
                "warmup_increment": 10,
                "warmup_max": 50,
            },
        },
        "send_window_start": "07:00",
        "send_window_end": "22:00",
        "blocked_domains": ["blocked1.com", "blocked2.org"],
        "do_not_contact_emails": ["dnc1@test.com", "dnc2@test.com"],
        "do_not_contact_lead_ids": [10, 20, 30],
    }
    
    # Update
    put_response = client.put("/api/cam/safety", json=modified_data)
    assert put_response.status_code == 200
    
    # Get again
    verify_response = client.get("/api/cam/safety")
    verified_data = verify_response.json()
    
    # Verify all fields preserved
    assert verified_data["per_channel_limits"]["email"]["max_per_day"] == 100
    assert verified_data["per_channel_limits"]["linkedin"]["warmup_start"] == 10
    assert verified_data["send_window_start"] == "07:00"
    assert verified_data["send_window_end"] == "22:00"
    assert set(verified_data["blocked_domains"]) == {"blocked1.com", "blocked2.org"}
    assert set(verified_data["do_not_contact_emails"]) == {"dnc1@test.com", "dnc2@test.com"}
    assert set(verified_data["do_not_contact_lead_ids"]) == {10, 20, 30}


def test_partial_update(client):
    """Test partial updates don't lose other fields."""
    # Get initial
    response = client.get("/api/cam/safety")
    data = response.json()
    
    # Only update blocked domains
    data["blocked_domains"] = ["newblock.com"]
    
    # Update
    update_response = client.put("/api/cam/safety", json=data)
    assert update_response.status_code == 200
    
    # Verify other fields unchanged
    verify_response = client.get("/api/cam/safety")
    verified_data = verify_response.json()
    
    assert verified_data["blocked_domains"] == ["newblock.com"]
    assert "email" in verified_data["per_channel_limits"]  # Should still exist
    assert verified_data["send_window_start"] == "09:00"  # Should be unchanged


# ==========================================
# TESTS: EDGE CASES
# ==========================================

def test_empty_send_window(client):
    """Test setting send window to None/null."""
    response = client.get("/api/cam/safety")
    data = response.json()
    
    # Remove send window
    data["send_window_start"] = None
    data["send_window_end"] = None
    
    # Update
    update_response = client.put("/api/cam/safety", json=data)
    assert update_response.status_code == 200
    
    # Verify
    verify_response = client.get("/api/cam/safety")
    verified_data = verify_response.json()
    
    assert verified_data["send_window_start"] is None
    assert verified_data["send_window_end"] is None


def test_empty_lists(client):
    """Test clearing all DNC/block lists."""
    # Set some values first
    response = client.get("/api/cam/safety")
    data = response.json()
    data["blocked_domains"] = ["test.com"]
    data["do_not_contact_emails"] = ["test@test.com"]
    data["do_not_contact_lead_ids"] = [1, 2]
    
    client.put("/api/cam/safety", json=data)
    
    # Now clear them
    data["blocked_domains"] = []
    data["do_not_contact_emails"] = []
    data["do_not_contact_lead_ids"] = []
    
    update_response = client.put("/api/cam/safety", json=data)
    assert update_response.status_code == 200
    
    # Verify cleared
    verify_response = client.get("/api/cam/safety")
    verified_data = verify_response.json()
    
    assert verified_data["blocked_domains"] == []
    assert verified_data["do_not_contact_emails"] == []
    assert verified_data["do_not_contact_lead_ids"] == []
