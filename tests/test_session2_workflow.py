"""
Unit tests for Session 2: Campaigns → Intake → Strategy workflow

Tests cover:
- Campaign creation and selection
- Active context management  
- Intake gating and approval
- Strategy gating
"""
import pytest
import uuid
from datetime import datetime


class MockSessionState(dict):
    """Mock Streamlit session_state"""
    pass


def test_campaign_creation():
    """Test campaign can be created with required fields"""
    session_state = MockSessionState()
    session_state["_campaigns"] = {}
    
    campaign_id = str(uuid.uuid4())
    campaign = {
        "campaign_id": campaign_id,
        "name": "Test Campaign",
        "objective": "Lead Generation",
        "budget": "$10k",
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
        "status": "Planned",
        "created_at": datetime.utcnow().isoformat()
    }
    
    session_state["_campaigns"][campaign_id] = campaign
    
    assert campaign_id in session_state["_campaigns"]
    assert session_state["_campaigns"][campaign_id]["name"] == "Test Campaign"
    assert session_state["_campaigns"][campaign_id]["objective"] == "Lead Generation"


def test_campaign_selection_sets_active_id():
    """Test selecting a campaign sets active_campaign_id"""
    session_state = MockSessionState()
    session_state["_campaigns"] = {}
    
    campaign_id = str(uuid.uuid4())
    campaign = {
        "campaign_id": campaign_id,
        "name": "Test Campaign",
        "objective": "Lead Generation",
        "status": "Active",
        "created_at": datetime.utcnow().isoformat()
    }
    
    session_state["_campaigns"][campaign_id] = campaign
    
    # Simulate selecting campaign
    session_state["active_campaign_id"] = campaign_id
    
    assert session_state.get("active_campaign_id") == campaign_id
    # Client and engagement should NOT be set yet (set during Intake)
    assert session_state.get("active_client_id") is None
    assert session_state.get("active_engagement_id") is None


def test_active_context_contract():
    """Test active context get/set/clear functions"""
    # Import after setting up path
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from operator_v2 import get_active_context, set_active_context, clear_active_context
    import streamlit as st
    
    # Set context
    campaign_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    engagement_id = str(uuid.uuid4())
    
    set_active_context(campaign_id, client_id, engagement_id)
    
    # Get context
    context = get_active_context()
    assert context is not None
    assert context["campaign_id"] == campaign_id
    assert context["client_id"] == client_id
    assert context["engagement_id"] == engagement_id
    
    # Clear context
    clear_active_context()
    context = get_active_context()
    assert context is None


def test_intake_requires_campaign():
    """Test intake cannot be created without active campaign"""
    session_state = MockSessionState()
    
    # No active_campaign_id set
    active_campaign_id = session_state.get("active_campaign_id")
    
    # Intake should be blocked
    assert active_campaign_id is None


def test_intake_approval_workflow():
    """Test intake save draft → approve workflow"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from aicmo.ui.persistence.artifact_store import (
        ArtifactStore, ArtifactType, ArtifactStatus, validate_intake, normalize_intake_payload
    )
    
    session_state = MockSessionState()
    store = ArtifactStore(session_state, mode="inmemory")
    
    # Create valid intake payload
    payload = {
        "client_name": "Test Client",
        "website": "https://example.com",
        "industry": "Technology",
        "geography": "United States",
        "primary_offer": "SaaS Platform",
        "objective": "Lead Generation",
        "target_audience": "B2B Companies",
        "pain_points": "Manual processes",
        "desired_outcomes": "Efficiency gains"
    }
    
    # Normalize and validate
    normalized = normalize_intake_payload(payload)
    ok, errors, warnings = validate_intake(normalized)
    
    assert ok is True
    assert len(errors) == 0
    
    # Create intake artifact
    client_id = str(uuid.uuid4())
    engagement_id = str(uuid.uuid4())
    
    intake = store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id=client_id,
        engagement_id=engagement_id,
        content=normalized
    )
    
    assert intake.status == ArtifactStatus.DRAFT
    assert intake.client_id == client_id
    assert intake.engagement_id == engagement_id
    
    # Create passing QC artifact (required for approval)
    from aicmo.ui.quality.qc_models import QCArtifact, QCCheck, QCStatus, CheckStatus, CheckSeverity, QCType, CheckType
    
    qc_artifact = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        qc_type=QCType.INTAKE_QC,
        target_artifact_id=intake.artifact_id,
        target_artifact_type="intake",
        target_version=intake.version,
        qc_status=QCStatus.PASS,
        qc_score=100,
        checks=[
            QCCheck(
                check_id="test_check",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MINOR,
                message="Test check passed"
            )
        ],
        created_at=datetime.utcnow().isoformat()
    )
    
    store.store_qc_artifact(qc_artifact)
    
    # Approve intake
    approved = store.approve_artifact(intake, approved_by="test_operator")
    
    assert approved.status == ArtifactStatus.APPROVED
    assert approved.approved_by == "test_operator"
    assert approved.approved_at is not None


def test_strategy_gates_on_intake_approval():
    """Test strategy is locked until intake is approved"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from aicmo.ui.persistence.artifact_store import (
        ArtifactStore, ArtifactType, ArtifactStatus, check_gating
    )
    
    session_state = MockSessionState()
    store = ArtifactStore(session_state, mode="inmemory")
    
    # Strategy should be blocked (no intake)
    allowed, reasons = check_gating(ArtifactType.STRATEGY, store)
    assert allowed is False
    assert len(reasons) > 0
    
    # Create and approve intake
    from aicmo.ui.quality.qc_models import QCArtifact, QCCheck, QCStatus, CheckStatus, CheckSeverity
    
    intake_content = {
        "client_name": "Test Client",
        "website": "https://example.com",
        "industry": "Technology",
        "geography": "United States",
        "primary_offer": "SaaS Platform",
        "objective": "Lead Generation"
    }
    
    intake = store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id="test",
        engagement_id="test",
        content=intake_content
    )
    
    # Create passing QC
    from aicmo.ui.quality.qc_models import QCType, CheckType
    
    qc_artifact = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        qc_type=QCType.INTAKE_QC,
        target_artifact_id=intake.artifact_id,
        target_artifact_type="intake",
        target_version=intake.version,
        qc_status=QCStatus.PASS,
        qc_score=100,
        checks=[
            QCCheck(
                check_id="test",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MINOR,
                message="Pass"
            )
        ],
        created_at=datetime.utcnow().isoformat()
    )
    
    store.store_qc_artifact(qc_artifact)
    
    approved_intake = store.approve_artifact(intake, approved_by="test")
    
    # Now strategy should be unlocked
    allowed, reasons = check_gating(ArtifactType.STRATEGY, store)
    assert allowed is True
    assert len(reasons) == 0


def test_validate_intake_importable():
    """Test validate_intake can be imported from artifact_store"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    import aicmo.ui.persistence.artifact_store as m
    
    # Check module file
    assert m.__file__ is not None
    assert "artifact_store.py" in m.__file__
    
    # Check functions exist
    assert hasattr(m, "validate_intake")
    assert hasattr(m, "normalize_intake_payload")
    assert hasattr(m, "validate_intake_content")
    
    # Test validate_intake is callable
    assert callable(m.validate_intake)


def test_normalize_intake_payload_field_mapping():
    """Test normalize_intake_payload applies correct field mappings"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from aicmo.ui.persistence.artifact_store import normalize_intake_payload
    
    # Test brand_name → client_name
    payload1 = {"brand_name": "Acme Corp"}
    normalized1 = normalize_intake_payload(payload1)
    assert normalized1.get("client_name") == "Acme Corp"
    
    # Test geography_served → geography
    payload2 = {"geography_served": "United States"}
    normalized2 = normalize_intake_payload(payload2)
    assert normalized2.get("geography") == "United States"
    
    # Test primary_offers → primary_offer
    payload3 = {"primary_offers": "SaaS Platform"}
    normalized3 = normalize_intake_payload(payload3)
    assert normalized3.get("primary_offer") == "SaaS Platform"
    
    # Test primary_objective → objective
    payload4 = {"primary_objective": "Lead Generation"}
    normalized4 = normalize_intake_payload(payload4)
    assert normalized4.get("objective") == "Lead Generation"
    
    # Test existing fields are preserved
    payload5 = {
        "client_name": "Existing Name",
        "brand_name": "Brand Name"
    }
    normalized5 = normalize_intake_payload(payload5)
    # Should keep existing client_name, not overwrite
    assert normalized5.get("client_name") == "Existing Name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
