"""
Tests for CAM Phase 8: Pipeline & Appointments API.

Tests pipeline management, lead stage updates, contact events, and appointment scheduling.
Uses file-based SQLite database to avoid session isolation issues.
"""

import pytest
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import main app and db models
from backend.main import app as main_app
import backend.routers.cam as cam_router_module
from aicmo.cam.db_models import Base, CampaignDB, LeadDB, ContactEventDB, AppointmentDB


# ==========================================
# TEST DATABASE SETUP (File-Based)
# ==========================================

TEST_DB_FILE = "./cam_pipeline_api_test.db"
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
def setup_cam_pipeline_api_test_db():
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
        ContactEventDB.__table__,
        AppointmentDB.__table__,
    ]:
        table.create(bind=engine, checkfirst=True)
    
    # Register dependency override
    main_app.dependency_overrides[cam_router_module.get_db] = override_get_db
    
    yield
    
    # Cleanup
    for table in [AppointmentDB.__table__, ContactEventDB.__table__, LeadDB.__table__, CampaignDB.__table__]:
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
        db.execute(text("DELETE FROM cam_appointments"))
        db.execute(text("DELETE FROM cam_contact_events"))
        db.execute(text("DELETE FROM cam_leads"))
        db.execute(text("DELETE FROM cam_campaigns"))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """Test client for API requests."""
    return TestClient(main_app)


@pytest.fixture
def sample_campaign():
    """Create a sample campaign directly in DB."""
    db = TestingSessionLocal()
    try:
        campaign = CampaignDB(
            name="Test Pipeline Campaign",
            description="Campaign for pipeline testing",
            target_niche="test",
            active=True,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign.id
    finally:
        db.close()


@pytest.fixture
def sample_lead(sample_campaign):
    """Create a sample lead directly in DB."""
    db = TestingSessionLocal()
    try:
        from aicmo.cam.domain import LeadSource, LeadStatus
        lead = LeadDB(
            campaign_id=sample_campaign,
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.MANUAL,
            status=LeadStatus.NEW,
            stage="NEW",  # Phase 8 stage field
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


# ==========================================
# TESTS: PIPELINE SUMMARY
# ==========================================

def test_get_pipeline_empty(client, sample_campaign):
    """Test pipeline summary for campaign with no leads."""
    response = client.get(f"/api/cam/pipeline?campaign_id={sample_campaign}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["campaign_id"] == sample_campaign
    assert data["new_count"] == 0
    assert data["contacted_count"] == 0
    assert data["replied_count"] == 0


def test_get_pipeline_with_leads(client, sample_campaign):
    """Test pipeline summary with leads in various stages."""
    # Create leads directly in DB with different stages
    from aicmo.cam.domain import LeadSource, LeadStatus
    db = TestingSessionLocal()
    try:
        leads = [
            LeadDB(campaign_id=sample_campaign, name="Lead1", email="l1@test.com", source=LeadSource.MANUAL, status=LeadStatus.NEW, stage="NEW"),
            LeadDB(campaign_id=sample_campaign, name="Lead2", email="l2@test.com", source=LeadSource.MANUAL, status=LeadStatus.NEW, stage="NEW"),
            LeadDB(campaign_id=sample_campaign, name="Lead3", email="l3@test.com", source=LeadSource.MANUAL, status=LeadStatus.CONTACTED, stage="CONTACTED"),
            LeadDB(campaign_id=sample_campaign, name="Lead4", email="l4@test.com", source=LeadSource.MANUAL, status=LeadStatus.REPLIED, stage="REPLIED"),
            LeadDB(campaign_id=sample_campaign, name="Lead5", email="l5@test.com", source=LeadSource.MANUAL, status=LeadStatus.QUALIFIED, stage="QUALIFIED"),
        ]
        for lead in leads:
            db.add(lead)
        db.commit()
    finally:
        db.close()
    
    response = client.get(f"/api/cam/pipeline?campaign_id={sample_campaign}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["new_count"] == 2
    assert data["contacted_count"] == 1
    assert data["replied_count"] == 1
    assert data["qualified_count"] == 1
    assert data["won_count"] == 0


# ==========================================
# TESTS: LEAD STAGE UPDATE
# ==========================================

def test_update_lead_stage_success(client, sample_lead):
    """Test updating lead stage via API."""
    response = client.post(
        f"/api/cam/leads/{sample_lead}/stage",
        json={"stage": "CONTACTED"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == sample_lead
    assert data["stage"] == "CONTACTED"
    
    # Verify in DB
    db = TestingSessionLocal()
    try:
        lead = db.query(LeadDB).filter(LeadDB.id == sample_lead).first()
        assert lead.stage == "CONTACTED"
    finally:
        db.close()


def test_update_lead_stage_invalid_lead(client):
    """Test updating non-existent lead."""
    response = client.post(
        "/api/cam/leads/99999/stage",
        json={"stage": "CONTACTED"},
    )
    
    assert response.status_code == 404


def test_update_lead_stage_progression(client, sample_lead):
    """Test lead stage progression through pipeline."""
    stages = ["CONTACTED", "REPLIED", "QUALIFIED", "WON"]
    
    for stage in stages:
        response = client.post(
            f"/api/cam/leads/{sample_lead}/stage",
            json={"stage": stage},
        )
        assert response.status_code == 200
        assert response.json()["stage"] == stage


# ==========================================
# TESTS: CONTACT EVENTS
# ==========================================

def test_log_contact_event_outbound(client, sample_lead):
    """Test logging outbound contact event."""
    response = client.post(
        f"/api/cam/leads/{sample_lead}/events",
        json={
            "channel": "email",
            "direction": "OUTBOUND",
            "summary": "Sent initial outreach email",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["lead_id"] == sample_lead
    assert data["channel"] == "email"
    assert data["direction"] == "OUTBOUND"
    assert data["summary"] == "Sent initial outreach email"
    assert "created_at" in data


def test_log_contact_event_inbound(client, sample_lead):
    """Test logging inbound contact event (reply)."""
    response = client.post(
        f"/api/cam/leads/{sample_lead}/events",
        json={
            "channel": "linkedin",
            "direction": "INBOUND",
            "summary": "Lead replied expressing interest",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["direction"] == "INBOUND"
    assert data["channel"] == "linkedin"


def test_log_contact_event_invalid_lead(client):
    """Test logging event for non-existent lead."""
    response = client.post(
        "/api/cam/leads/99999/events",
        json={
            "channel": "email",
            "direction": "OUTBOUND",
            "summary": "Test",
        },
    )
    
    assert response.status_code == 404


def test_multiple_contact_events(client, sample_lead):
    """Test logging multiple events for same lead."""
    events = [
        {"channel": "email", "direction": "OUTBOUND", "summary": "Initial email"},
        {"channel": "email", "direction": "INBOUND", "summary": "Lead replied"},
        {"channel": "linkedin", "direction": "OUTBOUND", "summary": "Follow-up on LinkedIn"},
    ]
    
    for event_data in events:
        response = client.post(
            f"/api/cam/leads/{sample_lead}/events",
            json=event_data,
        )
        assert response.status_code == 200
    
    # Verify in DB
    db = TestingSessionLocal()
    try:
        events = db.query(ContactEventDB).filter(ContactEventDB.lead_id == sample_lead).all()
        assert len(events) == 3
    finally:
        db.close()


# ==========================================
# TESTS: APPOINTMENTS
# ==========================================

def test_create_appointment(client, sample_lead):
    """Test creating an appointment."""
    scheduled_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
    
    response = client.post(
        "/api/cam/appointments",
        json={
            "lead_id": sample_lead,
            "scheduled_for": scheduled_time,
            "duration_minutes": 30,
            "location": "Zoom",
            "notes": "Demo call",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["lead_id"] == sample_lead
    assert data["duration_minutes"] == 30
    assert data["location"] == "Zoom"
    assert data["status"] == "SCHEDULED"


def test_create_appointment_invalid_lead(client):
    """Test creating appointment for non-existent lead."""
    scheduled_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
    
    response = client.post(
        "/api/cam/appointments",
        json={
            "lead_id": 99999,
            "scheduled_for": scheduled_time,
            "duration_minutes": 30,
        },
    )
    
    assert response.status_code == 404


def test_list_appointments_empty(client, sample_campaign):
    """Test listing appointments when none exist."""
    response = client.get(f"/api/cam/appointments?campaign_id={sample_campaign}")
    
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_appointments_with_data(client, sample_lead, sample_campaign):
    """Test listing appointments with existing appointments."""
    # Create appointments directly in DB
    db = TestingSessionLocal()
    try:
        future_time = datetime.utcnow() + timedelta(days=1)
        appt = AppointmentDB(
            lead_id=sample_lead,
            scheduled_for=future_time,
            duration_minutes=30,
            status="SCHEDULED",
        )
        db.add(appt)
        db.commit()
    finally:
        db.close()
    
    response = client.get(f"/api/cam/appointments?campaign_id={sample_campaign}")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lead_id"] == sample_lead


def test_list_appointments_only_upcoming(client, sample_lead, sample_campaign):
    """Test filtering appointments to only upcoming."""
    # Create past and future appointments
    db = TestingSessionLocal()
    try:
        past_time = datetime.utcnow() - timedelta(days=1)
        future_time = datetime.utcnow() + timedelta(days=1)
        
        db.add(AppointmentDB(lead_id=sample_lead, scheduled_for=past_time, duration_minutes=30, status="COMPLETED"))
        db.add(AppointmentDB(lead_id=sample_lead, scheduled_for=future_time, duration_minutes=30, status="SCHEDULED"))
        db.commit()
    finally:
        db.close()
    
    # Get only upcoming
    response = client.get(f"/api/cam/appointments?campaign_id={sample_campaign}&only_upcoming=true")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Should only return future appointment


def test_list_appointments_all(client, sample_lead, sample_campaign):
    """Test listing all appointments (past and future)."""
    # Create past and future appointments
    db = TestingSessionLocal()
    try:
        past_time = datetime.utcnow() - timedelta(days=1)
        future_time = datetime.utcnow() + timedelta(days=1)
        
        db.add(AppointmentDB(lead_id=sample_lead, scheduled_for=past_time, duration_minutes=30, status="COMPLETED"))
        db.add(AppointmentDB(lead_id=sample_lead, scheduled_for=future_time, duration_minutes=30, status="SCHEDULED"))
        db.commit()
    finally:
        db.close()
    
    # Get all appointments
    response = client.get(f"/api/cam/appointments?campaign_id={sample_campaign}&only_upcoming=false")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Should return both appointments


# ==========================================
# TESTS: INTEGRATION SCENARIOS
# ==========================================

def test_full_pipeline_workflow(client, sample_campaign):
    """Test complete pipeline workflow from discovery to appointment."""
    # Create a lead
    from aicmo.cam.domain import LeadSource, LeadStatus
    db = TestingSessionLocal()
    try:
        lead = LeadDB(
            campaign_id=sample_campaign,
            name="Workflow Lead",
            email="workflow@test.com",
            source=LeadSource.OTHER,
            status=LeadStatus.NEW,
            stage="NEW",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        lead_id = lead.id
    finally:
        db.close()
    
    # Check initial pipeline
    response = client.get(f"/api/cam/pipeline?campaign_id={sample_campaign}")
    assert response.json()["new_count"] == 1
    
    # Update to CONTACTED
    response = client.post(f"/api/cam/leads/{lead_id}/stage", json={"stage": "CONTACTED"})
    assert response.status_code == 200
    
    # Log outbound event
    response = client.post(
        f"/api/cam/leads/{lead_id}/events",
        json={"channel": "email", "direction": "OUTBOUND", "summary": "Initial outreach"},
    )
    assert response.status_code == 200
    
    # Update to REPLIED
    response = client.post(f"/api/cam/leads/{lead_id}/stage", json={"stage": "REPLIED"})
    assert response.status_code == 200
    
    # Log inbound event
    response = client.post(
        f"/api/cam/leads/{lead_id}/events",
        json={"channel": "email", "direction": "INBOUND", "summary": "Lead expressed interest"},
    )
    assert response.status_code == 200
    
    # Create appointment
    scheduled_time = (datetime.utcnow() + timedelta(days=3)).isoformat()
    response = client.post(
        "/api/cam/appointments",
        json={
            "lead_id": lead_id,
            "scheduled_for": scheduled_time,
            "duration_minutes": 45,
            "location": "Zoom",
        },
    )
    assert response.status_code == 201
    
    # Verify final pipeline state
    response = client.get(f"/api/cam/pipeline?campaign_id={sample_campaign}")
    data = response.json()
    assert data["new_count"] == 0
    assert data["replied_count"] == 1
    
    # Verify appointment exists
    response = client.get(f"/api/cam/appointments?campaign_id={sample_campaign}")
    assert len(response.json()) == 1
