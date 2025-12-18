"""
QC-on-Approve Tests

Proves that approval workflow automatically runs QC if missing.

Test Coverage:
1. Missing QC → auto-runs and persists QC artifact
2. QC FAIL → blocks approval with visible issues
3. QC PASS → proceeds to approve
4. Tab ID canonicalization (display labels normalized)
5. Store namespace consistency (QC persisted to same store)
"""
import pytest
from aicmo.ui.persistence.artifact_store import (
    ArtifactStore,
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactValidationError
)
from aicmo.ui.qc_on_approve import (
    ensure_qc_for_artifact,
    canonicalize_tab_id,
    TAB_INTAKE,
    TAB_STRATEGY
)
from aicmo.ui.quality.qc_models import QCStatus


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def mock_session():
    """Create mock session state"""
    return {}


@pytest.fixture
def store(mock_session):
    """Create ArtifactStore with mock session"""
    return ArtifactStore(mock_session, mode="inmemory")


def create_valid_intake(store, client_id="client-test", engagement_id="eng-test") -> Artifact:
    """Create valid intake artifact (all required fields present)"""
    return store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "client_name": "Test Company",
            "website": "https://testcompany.com",
            "industry": "Technology",
            "geography": "United States",
            "primary_offer": "SaaS Platform",
            "objective": "Leads",  # Required
            "target_audience": "B2B Enterprise",
            "pain_points": ["Manual processes", "Data silos"],
            "desired_outcomes": ["Automation", "Integration"],
            "compliance_requirements": "GDPR compliant",
            "proof_assets": "3 case studies",
            "pricing_logic": "$99-$499/mo",
            "brand_voice": "Professional"
        }
    )


def create_invalid_intake(store, client_id="client-test", engagement_id="eng-test") -> Artifact:
    """Create invalid intake artifact (missing required fields)"""
    return store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "client_name": "Test Company",
            # Missing: website, industry, geography, etc.
        }
    )


# ===================================================================
# Test 1: QC Auto-Run When Missing
# ===================================================================

def test_ensure_qc_creates_qc_when_missing(store):
    """
    QC-on-Approve: Missing QC → auto-runs and persists QC artifact.
    Proves approval workflow can automatically generate missing QC.
    """
    # Create valid intake (no QC)
    intake = create_valid_intake(store)
    
    # Confirm no QC exists
    existing_qc = store.get_qc_for_artifact(intake)
    assert existing_qc is None, "QC should not exist initially"
    
    # Call ensure_qc_for_artifact (simulates approval click)
    qc_artifact = ensure_qc_for_artifact(
        store=store,
        artifact=intake,
        client_id="client-test",
        engagement_id="eng-test",
        operator_id="test_operator"
    )
    
    # Verify QC artifact was created
    assert qc_artifact is not None, "QC artifact should be created"
    assert qc_artifact.target_artifact_id == intake.artifact_id
    assert qc_artifact.target_version == intake.version
    
    # Verify QC artifact is persisted in store
    fetched_qc = store.get_qc_for_artifact(intake)
    assert fetched_qc is not None, "QC should be retrievable from store"
    assert fetched_qc.qc_artifact_id == qc_artifact.qc_artifact_id


def test_ensure_qc_returns_existing_qc_when_present(store):
    """
    QC-on-Approve: Existing QC → returns existing (no duplicate).
    Proves idempotency.
    """
    from aicmo.ui.quality.qc_service import run_and_persist_qc_for
    
    # Create intake and run QC manually
    intake = create_valid_intake(store)
    original_qc = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    
    # Call ensure_qc_for_artifact
    returned_qc = ensure_qc_for_artifact(
        store=store,
        artifact=intake,
        client_id="client-test",
        engagement_id="eng-test",
        operator_id="test_operator"
    )
    
    # Should return same QC artifact (no duplicate)
    assert returned_qc.qc_artifact_id == original_qc.qc_artifact_id


# ===================================================================
# Test 2: QC FAIL Blocks Approval
# ===================================================================

def test_qc_fail_blocks_approval(store):
    """
    QC-on-Approve: QC FAIL → blocks approval with visible issues.
    Proves failing QC prevents approval.
    """
    # Create invalid intake (missing required fields)
    intake = create_invalid_intake(store)
    
    # Ensure QC (will fail due to missing fields)
    qc_artifact = ensure_qc_for_artifact(
        store=store,
        artifact=intake,
        client_id="client-test",
        engagement_id="eng-test",
        operator_id="test_operator"
    )
    
    # Verify QC status is FAIL
    assert qc_artifact.qc_status == QCStatus.FAIL, "QC should fail for invalid intake"
    
    # Verify blocker checks are present
    blocker_checks = [
        check for check in qc_artifact.checks
        if check.status.value == "FAIL" and check.severity.value == "BLOCKER"
    ]
    assert len(blocker_checks) > 0, "Should have blocker issues"
    
    # Attempt approval (should fail)
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake, approved_by="test_operator")
    
    # Verify failure is due to QC FAIL (blocker checks)
    errors = exc_info.value.errors
    assert any("BLOCKER" in err or "Missing required field" in err for err in errors), \
        f"Should fail due to blocker issues. Got errors: {errors}"


# ===================================================================
# Test 3: QC PASS Allows Approval
# ===================================================================

def test_qc_pass_allows_approval(store):
    """
    QC-on-Approve: QC PASS → proceeds to approve.
    Proves passing QC enables approval.
    """
    # Create valid intake
    intake = create_valid_intake(store)
    
    # Ensure QC (will pass for valid intake)
    qc_artifact = ensure_qc_for_artifact(
        store=store,
        artifact=intake,
        client_id="client-test",
        engagement_id="eng-test",
        operator_id="test_operator"
    )
    
    # Verify QC status is PASS
    assert qc_artifact.qc_status == QCStatus.PASS, "QC should pass for valid intake"
    
    # Attempt approval (should succeed)
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Verify approval succeeded
    assert approved_intake.status == ArtifactStatus.APPROVED
    assert approved_intake.approved_by == "test_operator"


# ===================================================================
# Test 4: Tab ID Canonicalization
# ===================================================================

def test_canonicalize_tab_id_display_labels():
    """
    Tab ID Canonicalization: Display labels → canonical IDs.
    Proves "Client Intake" normalizes to "intake".
    """
    # Display label to canonical mapping
    assert canonicalize_tab_id("Client Intake") == TAB_INTAKE
    assert canonicalize_tab_id("Intake") == TAB_INTAKE
    assert canonicalize_tab_id("Strategy Contract") == TAB_STRATEGY
    assert canonicalize_tab_id("Strategy") == TAB_STRATEGY


def test_canonicalize_tab_id_already_canonical():
    """
    Tab ID Canonicalization: Canonical IDs pass through unchanged.
    """
    assert canonicalize_tab_id("intake") == TAB_INTAKE
    assert canonicalize_tab_id("strategy") == TAB_STRATEGY


def test_canonicalize_tab_id_fallback():
    """
    Tab ID Canonicalization: Unknown labels fallback to lowercase.
    """
    assert canonicalize_tab_id("Unknown Label") == "unknown label"


# ===================================================================
# Test 5: Store Namespace Consistency
# ===================================================================

def test_qc_persisted_to_same_store_namespace(store):
    """
    Store Namespace Consistency: QC persisted to same store as artifact.
    Proves QC artifact is retrievable using same store instance.
    """
    # Create intake in specific namespace
    intake = create_valid_intake(store, client_id="namespace-test", engagement_id="eng-1")
    
    # Ensure QC
    qc_artifact = ensure_qc_for_artifact(
        store=store,
        artifact=intake,
        client_id="namespace-test",
        engagement_id="eng-1",
        operator_id="test_operator"
    )
    
    # Retrieve QC using same store instance
    fetched_qc = store.get_qc_for_artifact(intake)
    
    # Verify QC is retrievable (same namespace)
    assert fetched_qc is not None, "QC should be retrievable from same store"
    assert fetched_qc.qc_artifact_id == qc_artifact.qc_artifact_id
    assert qc_artifact.target_artifact_id == intake.artifact_id


# ===================================================================
# Test 6: Version Lock Enforcement
# ===================================================================

def test_ensure_qc_regenerates_when_version_mismatch(store):
    """
    QC Version Lock: Stale QC → regenerates for new version.
    Proves QC is regenerated when artifact version changes.
    """
    from aicmo.ui.quality.qc_service import run_and_persist_qc_for
    
    # Create intake and run QC for v1
    intake = create_valid_intake(store)
    v1_qc = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    
    # Update intake (creates v2)
    intake_v2 = store.update_artifact(
        intake,
        content={**intake.content, "client_name": "Updated Company"},
        notes=intake.notes,
        increment_version=True
    )
    
    # Ensure QC for v2 (should regenerate)
    v2_qc = ensure_qc_for_artifact(
        store=store,
        artifact=intake_v2,
        client_id="client-test",
        engagement_id="eng-test",
        operator_id="test_operator"
    )
    
    # Verify new QC was created for v2
    assert v2_qc.qc_artifact_id != v1_qc.qc_artifact_id, "Should create new QC for v2"
    assert v2_qc.target_version == intake_v2.version
    assert v2_qc.target_version != v1_qc.target_version


# ===================================================================
# Test 7: Full Approval Workflow
# ===================================================================

def test_full_approval_workflow_with_qc_on_approve(store):
    """
    Full Workflow: Create → Ensure QC → Approve.
    Proves complete approval workflow with QC-on-Approve.
    """
    # Step 1: Create valid intake (no QC)
    intake = create_valid_intake(store)
    assert intake.status == ArtifactStatus.DRAFT
    
    # Step 2: Ensure QC (auto-run)
    qc_artifact = ensure_qc_for_artifact(
        store=store,
        artifact=intake,
        client_id="client-test",
        engagement_id="eng-test",
        operator_id="test_operator"
    )
    assert qc_artifact.qc_status == QCStatus.PASS
    
    # Step 3: Approve (should succeed with QC present)
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    assert approved_intake.status == ArtifactStatus.APPROVED
    
    # Step 4: Verify QC artifact persisted
    final_qc = store.get_qc_for_artifact(approved_intake)
    assert final_qc is not None
    assert final_qc.qc_artifact_id == qc_artifact.qc_artifact_id
