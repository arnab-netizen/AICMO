"""
Comprehensive tests for Quality Control layer enforcement.

Tests:
    - QC model creation and status calculation
    - Deterministic checks for all artifact types
    - QC gate enforcement in approval flow
    - Version locking between QC and target artifacts
"""
import pytest
import uuid
from datetime import datetime
from typing import Dict, Any

from aicmo.ui.quality.qc_models import (
    QCArtifact,
    QCCheck,
    QCSummary,
    QCStatus,
    QCType,
    CheckStatus,
    CheckSeverity,
    CheckType
)
from aicmo.ui.quality.deterministic_checks import (
    validate_intake_qc,
    validate_strategy_qc,
    validate_creatives_qc,
    validate_execution_qc,
    validate_delivery_qc,
    run_deterministic_checks
)
from aicmo.ui.persistence.artifact_store import (
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactStore,
    ArtifactValidationError
)


# Helper function to create valid intake content
def create_valid_intake_content() -> Dict[str, Any]:
    """Create valid intake content that passes basic validation"""
    return {
        "brand_name": "Test Brand",
        "client_name": "Test Client",
        "website": "https://test.com",
        "industry": "Technology",
        "geography": "North America",
        "primary_offer": "SaaS Product",
        "objective": "Awareness",
        "target_audience": "B2B Decision Makers",
        "offer": "Free Trial"
    }


# ============================================================================
# QC MODEL TESTS
# ============================================================================

def test_qc_check_creation():
    """Test QCCheck creation and serialization"""
    check = QCCheck(
        check_id="test_check",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.FAIL,
        severity=CheckSeverity.BLOCKER,
        message="Test failed",
        evidence="Test evidence",
        auto_fixable=True,
        fix_instruction="Fix this"
    )
    
    assert check.check_id == "test_check"
    assert check.severity == CheckSeverity.BLOCKER
    
    # Test serialization
    check_dict = check.to_dict()
    assert check_dict["check_id"] == "test_check"
    assert check_dict["severity"] == "BLOCKER"
    
    # Test deserialization
    check2 = QCCheck.from_dict(check_dict)
    assert check2.check_id == check.check_id
    assert check2.severity == check.severity


def test_qc_artifact_status_calculation():
    """Test that any BLOCKER with FAIL → qc_status = FAIL"""
    qc = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        qc_type=QCType.STRATEGY_QC,
        target_artifact_id="art_123",
        target_artifact_type="STRATEGY",
        target_version=1,
        qc_status=QCStatus.PASS,  # Will be overwritten
        qc_score=100
    )
    
    # Add one blocker FAIL
    qc.checks.append(QCCheck(
        check_id="blocker_fail",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.FAIL,
        severity=CheckSeverity.BLOCKER,
        message="Critical issue"
    ))
    
    qc.compute_status_and_summary()
    
    assert qc.qc_status == QCStatus.FAIL
    assert qc.summary.blockers == 1


def test_qc_artifact_score_calculation():
    """Test QC score computation"""
    qc = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        qc_type=QCType.STRATEGY_QC,
        target_artifact_id="art_123",
        target_artifact_type="STRATEGY",
        target_version=1,
        qc_status=QCStatus.PASS,
        qc_score=100
    )
    
    # Start at 100
    # Add BLOCKER FAIL (-30)
    qc.checks.append(QCCheck(
        check_id="blocker1",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.FAIL,
        severity=CheckSeverity.BLOCKER,
        message="Blocker"
    ))
    
    # Add MAJOR FAIL (-10)
    qc.checks.append(QCCheck(
        check_id="major1",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.FAIL,
        severity=CheckSeverity.MAJOR,
        message="Major"
    ))
    
    qc.compute_score()
    
    # 100 - 30 - 10 = 60
    assert qc.qc_score == 60


def test_qc_artifact_serialization():
    """Test QCArtifact to/from dict"""
    qc = QCArtifact(
        qc_artifact_id="qc_123",
        qc_type=QCType.INTAKE_QC,
        target_artifact_id="art_456",
        target_artifact_type="INTAKE",
        target_version=2,
        qc_status=QCStatus.PASS,
        qc_score=85
    )
    
    qc.checks.append(QCCheck(
        check_id="test",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.PASS,
        severity=CheckSeverity.BLOCKER,
        message="OK"
    ))
    
    qc_dict = qc.to_dict()
    qc2 = QCArtifact.from_dict(qc_dict)
    
    assert qc2.qc_artifact_id == qc.qc_artifact_id
    assert qc2.target_version == qc.target_version
    assert len(qc2.checks) == 1


# ============================================================================
# DETERMINISTIC CHECKS TESTS
# ============================================================================

def test_intake_missing_required_fields():
    """Test intake QC detects missing required fields"""
    content = {
        "brand_name": "Test Brand",
        "objective": "Awareness",
        # Missing target_audience and offer
    }
    
    checks = validate_intake_qc(content)
    
    # Should have check for required fields
    required_check = next(c for c in checks if c.check_id == "intake_required_fields")
    assert required_check.status == CheckStatus.FAIL
    assert required_check.severity == CheckSeverity.BLOCKER


def test_intake_zero_ads_budget():
    """Test intake QC blocks zero ads budget when ads job requested"""
    content = {
        "brand_name": "Test",
        "objective": "Awareness",
        "target_audience": "Everyone",
        "offer": "Product",
        "jobs_requested": ["ads", "content"],
        "budget": {"ads_budget": 0}
    }
    
    checks = validate_intake_qc(content)
    
    budget_check = next(c for c in checks if c.check_id == "intake_budget_sanity")
    assert budget_check.status == CheckStatus.FAIL
    assert budget_check.severity == CheckSeverity.BLOCKER


def test_strategy_missing_sections():
    """Test strategy QC detects missing required sections"""
    content = {
        "icp": {"segments": []},
        "positioning": {"statement": "Test"},
        # Missing messaging, pillars, platform_plan, ctas, measurement
    }
    
    checks = validate_strategy_qc(content)
    
    sections_check = next(c for c in checks if c.check_id == "strategy_required_sections")
    assert sections_check.status == CheckStatus.FAIL
    assert sections_check.severity == CheckSeverity.BLOCKER


def test_strategy_placeholder_text():
    """Test strategy QC detects placeholder text"""
    content = {
        "icp": {"segments": ["TBD"]},
        "positioning": {"statement": "TODO: fill in"},
        "messaging": "lorem ipsum",
        "pillars": [],
        "platform_plan": {},
        "ctas": [],
        "measurement": {}
    }
    
    checks = validate_strategy_qc(content)
    
    placeholder_check = next(c for c in checks if c.check_id == "strategy_no_placeholders")
    assert placeholder_check.status == CheckStatus.FAIL
    assert placeholder_check.severity == CheckSeverity.BLOCKER
    assert placeholder_check.auto_fixable == True


def test_creatives_platform_constraints_twitter():
    """Test creatives QC enforces Twitter character limit"""
    content = {
        "format": "image",
        "platform": "twitter",
        "caption": "x" * 300,  # Exceeds 280 char limit
        "image_url": "http://example.com/image.png"
    }
    
    checks = validate_creatives_qc(content)
    
    constraints_check = next(c for c in checks if c.check_id == "creatives_platform_constraints")
    assert constraints_check.status == CheckStatus.FAIL
    assert constraints_check.severity == CheckSeverity.BLOCKER


def test_creatives_missing_cta():
    """Test creatives QC detects missing CTA"""
    content = {
        "format": "image",
        "platform": "instagram",
        "caption": "Just a caption with no call to action",
        "image_url": "http://example.com/image.png"
    }
    
    checks = validate_creatives_qc(content)
    
    cta_check = next(c for c in checks if c.check_id == "creatives_cta_present")
    assert cta_check.status == CheckStatus.FAIL
    assert cta_check.severity == CheckSeverity.MAJOR
    assert cta_check.auto_fixable == True


def test_execution_missing_cta_in_posts():
    """Test execution QC detects posts without CTA"""
    content = {
        "posts": [
            {
                "platform": "instagram",
                "caption": "Shop now at our store",  # Has CTA
                "date": "2024-01-01"
            },
            {
                "platform": "instagram",
                "caption": "Just a nice picture",  # No CTA
                "date": "2024-01-02"
            }
        ]
    }
    
    checks = validate_execution_qc(content)
    
    cta_check = next(c for c in checks if c.check_id == "execution_cta_every_post")
    assert cta_check.status == CheckStatus.FAIL
    assert cta_check.severity == CheckSeverity.BLOCKER
    assert "2" in cta_check.message  # Post 2 missing CTA


def test_delivery_missing_sections():
    """Test delivery QC detects missing required sections"""
    content = {
        "executive_summary": "Summary here",
        # Missing campaign_overview, deliverables, timeline, next_steps
    }
    
    checks = validate_delivery_qc(content)
    
    sections_check = next(c for c in checks if c.check_id == "delivery_required_sections")
    assert sections_check.status == CheckStatus.FAIL
    assert sections_check.severity == CheckSeverity.BLOCKER


def test_delivery_internal_notes_leaked():
    """Test delivery QC detects leaked internal notes"""
    content = {
        "executive_summary": "Campaign went well",
        "campaign_overview": "Internal: do not share this with client",
        "deliverables": {},
        "timeline": {},
        "next_steps": "FIXME: add more details"
    }
    
    checks = validate_delivery_qc(content)
    
    internal_check = next(c for c in checks if c.check_id == "delivery_no_internal_notes")
    assert internal_check.status == CheckStatus.FAIL
    assert internal_check.severity == CheckSeverity.BLOCKER


def test_run_deterministic_checks_dispatcher():
    """Test dispatcher routes to correct check function"""
    intake_content = {
        "brand_name": "Test",
        "objective": "Awareness",
        "target_audience": "Users",
        "offer": "Product"
    }
    
    checks = run_deterministic_checks("INTAKE", intake_content)
    
    assert len(checks) > 0
    assert all(isinstance(c, QCCheck) for c in checks)
    
    # Should have intake-specific checks
    check_ids = [c.check_id for c in checks]
    assert "intake_required_fields" in check_ids


# ============================================================================
# APPROVAL ENFORCEMENT TESTS
# ============================================================================

def test_cannot_approve_without_qc(tmp_path):
    """Test that approval fails if QC artifact does not exist"""
    session_state = {}
    store = ArtifactStore(session_state)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Create intake artifact
    intake = Artifact(
        artifact_id=str(uuid.uuid4()),
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content=create_valid_intake_content(),
        source_lineage={}
    )
    
    # Try to approve without QC - should fail
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake)
    
    errors = exc_info.value.errors
    assert any("No QC artifact found" in e for e in errors)


def test_cannot_approve_with_qc_fail():
    """Test that approval fails if QC status is FAIL"""
    session_state = {"_qc_artifacts": {}}
    store = ArtifactStore(session_state)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Create intake artifact
    intake = Artifact(
        artifact_id="art_123",
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content=create_valid_intake_content(),
        source_lineage={}
    )
    
    # Create failing QC artifact
    qc = QCArtifact(
        qc_artifact_id="qc_123",
        qc_type=QCType.INTAKE_QC,
        target_artifact_id="art_123",
        target_artifact_type="INTAKE",
        target_version=1,
        qc_status=QCStatus.FAIL,  # FAIL status
        qc_score=40
    )
    
    qc.checks.append(QCCheck(
        check_id="blocker1",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.FAIL,
        severity=CheckSeverity.BLOCKER,
        message="Critical failure"
    ))
    
    store.store_qc_artifact(qc)
    
    # Try to approve - should fail
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake)
    
    errors = exc_info.value.errors
    assert any("QC failed" in e for e in errors)
    assert any("blocker" in e.lower() for e in errors)


def test_cannot_approve_with_qc_version_mismatch():
    """Test that approval fails if QC target_version doesn't match artifact version"""
    session_state = {"_qc_artifacts": {}}
    store = ArtifactStore(session_state)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Create intake artifact at version 2
    intake = Artifact(
        artifact_id="art_123",
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.INTAKE,
        version=2,  # Version 2
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content=create_valid_intake_content(),
        source_lineage={}
    )
    
    # Create QC artifact for version 1 (mismatch)
    qc = QCArtifact(
        qc_artifact_id="qc_123",
        qc_type=QCType.INTAKE_QC,
        target_artifact_id="art_123",
        target_artifact_type="INTAKE",
        target_version=1,  # Version 1 (mismatch!)
        qc_status=QCStatus.PASS,
        qc_score=100
    )
    
    # Store QC with key for version 1
    session_state["_qc_artifacts"]["art_123_v1"] = qc.to_dict()
    
    # Try to approve version 2 artifact - should fail
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake)
    
    errors = exc_info.value.errors
    # Should fail because QC for v2 doesn't exist
    assert any("No QC artifact found" in e for e in errors)


def test_can_approve_with_passing_qc():
    """Test that approval succeeds with passing QC"""
    session_state = {"_qc_artifacts": {}}
    store = ArtifactStore(session_state)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Create intake artifact
    intake = Artifact(
        artifact_id="art_123",
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content=create_valid_intake_content(),
        source_lineage={}
    )
    
    # Create passing QC artifact
    qc = QCArtifact(
        qc_artifact_id="qc_123",
        qc_type=QCType.INTAKE_QC,
        target_artifact_id="art_123",
        target_artifact_type="INTAKE",
        target_version=1,
        qc_status=QCStatus.PASS,
        qc_score=100
    )
    
    qc.checks.append(QCCheck(
        check_id="check1",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.PASS,
        severity=CheckSeverity.BLOCKER,
        message="All good"
    ))
    
    store.store_qc_artifact(qc)
    
    # Approval should succeed
    approved = store.approve_artifact(intake)
    
    assert approved.status == ArtifactStatus.APPROVED
    assert approved.approved_by == "operator"


def test_can_approve_with_warn_qc():
    """Test that approval succeeds with QC status WARN (not FAIL)"""
    session_state = {"_qc_artifacts": {}}
    store = ArtifactStore(session_state)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Create intake artifact
    intake = Artifact(
        artifact_id="art_123",
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content=create_valid_intake_content(),
        source_lineage={}
    )
    
    # Create WARN QC artifact (not FAIL)
    qc = QCArtifact(
        qc_artifact_id="qc_123",
        qc_type=QCType.INTAKE_QC,
        target_artifact_id="art_123",
        target_artifact_type="INTAKE",
        target_version=1,
        qc_status=QCStatus.WARN,  # WARN is acceptable
        qc_score=85
    )
    
    qc.checks.append(QCCheck(
        check_id="warning1",
        check_type=CheckType.DETERMINISTIC,
        status=CheckStatus.WARN,
        severity=CheckSeverity.MAJOR,
        message="Minor issue"
    ))
    
    store.store_qc_artifact(qc)
    
    # Approval should succeed (WARN doesn't block)
    approved = store.approve_artifact(intake)
    
    assert approved.status == ArtifactStatus.APPROVED


# ============================================================================
# QC INTEGRATION TESTS
# ============================================================================

def test_qc_storage_and_retrieval():
    """Test storing and retrieving QC artifacts"""
    session_state = {}
    store = ArtifactStore(session_state)
    
    qc = QCArtifact(
        qc_artifact_id="qc_123",
        qc_type=QCType.STRATEGY_QC,
        target_artifact_id="art_456",
        target_artifact_type="STRATEGY",
        target_version=3,
        qc_status=QCStatus.PASS,
        qc_score=95
    )
    
    store.store_qc_artifact(qc)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Create artifact to retrieve QC for
    artifact = Artifact(
        artifact_id="art_456",
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.STRATEGY,
        version=3,
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content={},
        source_lineage={}
    )
    
    retrieved_qc = store.get_qc_for_artifact(artifact)
    
    assert retrieved_qc is not None
    assert retrieved_qc.qc_artifact_id == "qc_123"
    assert retrieved_qc.target_version == 3
    assert retrieved_qc.qc_score == 95


def test_end_to_end_qc_enforcement_flow():
    """
    End-to-end test: Create artifact → Run QC → Fail → Cannot approve
    """
    session_state = {}
    store = ArtifactStore(session_state)
    
    now_iso = datetime.utcnow().isoformat()
    
    # Step 1: Create strategy artifact with placeholder text
    strategy = Artifact(
        artifact_id="strat_1",
        client_id="client1",
        engagement_id="eng1",
        artifact_type=ArtifactType.STRATEGY,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at=now_iso,
        updated_at=now_iso,
        content={
            "icp": {"segments": ["TBD"]},  # Placeholder!
            "positioning": {"statement": "TODO"},
            "messaging": "lorem ipsum",
            "content_pillars": [],  # Use correct field name
            "platform_plan": {},
            "cta_rules": [],  # Use correct field name
            "measurement": {}
        },
        source_lineage={"intake": {"artifact_id": "intake_1", "approved_version": 1, "approved_at": now_iso}}
    )
    
    # Step 2: Run deterministic QC
    checks = validate_strategy_qc(strategy.content)
    
    # Step 3: Create QC artifact
    qc = QCArtifact(
        qc_artifact_id="qc_strat_1",
        qc_type=QCType.STRATEGY_QC,
        target_artifact_id="strat_1",
        target_artifact_type="STRATEGY",
        target_version=1,
        qc_status=QCStatus.PASS,  # Will be computed
        qc_score=100,
        checks=checks
    )
    
    qc.compute_status_and_summary()
    qc.compute_score()
    
    # QC should fail due to placeholder text
    assert qc.qc_status == QCStatus.FAIL
    
    store.store_qc_artifact(qc)
    
    # Step 4: Try to approve - should fail
    with pytest.raises(ArtifactValidationError) as exc_info:
        # Need to mock intake artifact for lineage validation
        intake = Artifact(
            artifact_id="intake_1",
            client_id="client1",
            engagement_id="eng1",
            artifact_type=ArtifactType.INTAKE,
            version=1,
            status=ArtifactStatus.APPROVED,
            created_at=now_iso,
            updated_at=now_iso,
            content=create_valid_intake_content(),
            source_lineage={}
        )
        session_state["artifact_intake"] = intake.to_dict()
        session_state["_artifacts"] = {intake.artifact_id: intake.to_dict()}
        
        store.approve_artifact(strategy)
    
    errors = exc_info.value.errors
    assert any("QC failed" in e for e in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
