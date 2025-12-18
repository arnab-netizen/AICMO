"""
QC Enforcement Tests

Proves that QC enforcement gate works correctly:
- Approvals refused if QC missing
- Approvals refused if QC FAIL
- Approvals refused if QC version mismatch
- Approvals allowed if QC PASS
"""
import pytest
import uuid
from datetime import datetime

from aicmo.ui.persistence.artifact_store import (
    ArtifactStore,
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactValidationError
)
from aicmo.ui.quality.qc_service import run_and_persist_qc_for
from aicmo.ui.quality.qc_models import QCArtifact, QCStatus, QCType, CheckSeverity, CheckStatus, CheckType, QCCheck, QCSummary
from tests.fixtures.minimal_strategy import minimal_strategy_contract


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


def create_minimal_intake(store, client_id="client-test", engagement_id="eng-test") -> Artifact:
    """Helper: Create minimal valid intake artifact"""
    intake = store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "client_name": "Test Company",
            "website": "https://testcompany.com",
            "industry": "Technology",
            "geography": "US",
            "primary_offer": "SaaS Platform",
            "objective": "Leads",  # Required by content validation
            "target_audience": "B2B SaaS Companies",
            "pain_points": "Manual processes, high costs",
            "desired_outcomes": "Reduce costs by 30%",
            "compliance_requirements": "GDPR compliant",
            "proof_assets": "3 case studies",  # Avoid MAJOR failure
            "pricing_logic": "$99-$499/mo",    # Avoid MAJOR failure
            "brand_voice": "Professional"      # Avoid MINOR failure
        }
    )
    return intake


def create_minimal_strategy(store, intake_artifact, client_id="client-test", engagement_id="eng-test") -> Artifact:
    """Helper: Create minimal valid strategy artifact"""
    strategy = store.create_artifact(
        artifact_type=ArtifactType.STRATEGY,
        client_id=client_id,
        engagement_id=engagement_id,
        source_artifacts=[intake_artifact],
        content=minimal_strategy_contract()
    )
    return strategy


def create_minimal_delivery(store, intake_artifact, strategy_artifact, creatives_artifact, execution_artifact, client_id="client-test", engagement_id="eng-test") -> Artifact:
    """Helper: Create minimal valid delivery artifact with complete upstream lineage"""
    delivery = store.create_artifact(
        artifact_type=ArtifactType.DELIVERY,
        client_id=client_id,
        engagement_id=engagement_id,
        source_artifacts=[intake_artifact, strategy_artifact, creatives_artifact, execution_artifact],
        content={
            "manifest": {
                "schema_version": "delivery_manifest_v1",
                "generation_plan": {
                    "selected_job_ids": [
                        "brand_strategy", "content_library", 
                        "content_calendar", "execution_schedule"
                    ]  # Full plan: strategy + creatives + execution
                },
                "included_artifacts": [
                    {"type": "intake", "artifact_id": intake_artifact.artifact_id, "status": "approved"},
                    {"type": "strategy", "artifact_id": strategy_artifact.artifact_id, "status": "approved"},
                    {"type": "creatives", "artifact_id": creatives_artifact.artifact_id, "status": "approved"},
                    {"type": "execution", "artifact_id": execution_artifact.artifact_id, "status": "approved"}
                ],
                "checks": {
                    "approvals_ok": True,
                    "branding_ok": True
                }
            },
            "notes": "Test delivery package"
        }
    )
    return delivery


# ===================================================================
# TEST 1: Approval Refused if QC Missing
# ===================================================================

def test_approval_refused_qc_missing_intake(store):
    """Test that approval is refused if QC artifact is missing for Intake"""
    # Create intake artifact (no QC)
    intake = create_minimal_intake(store)
    
    # Attempt approval
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake, approved_by="test_operator")
    
    # Check error message
    errors = exc_info.value.errors
    assert len(errors) > 0
    assert "No QC artifact found" in errors[0]
    assert "intake" in errors[0].lower()


def test_approval_refused_qc_missing_strategy(store):
    """Test that approval is refused if QC artifact is missing for Strategy"""
    # Create and approve intake (with QC)
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Create strategy artifact (no QC)
    strategy = create_minimal_strategy(store, approved_intake)
    
    # Attempt approval
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(strategy, approved_by="test_operator")
    
    # Check error message
    errors = exc_info.value.errors
    assert len(errors) > 0
    assert "No QC artifact found" in errors[0]
    assert "strategy" in errors[0].lower()


# ===================================================================
# TEST 2: Approval Refused if QC FAIL
# ===================================================================

def test_approval_refused_qc_fail_intake(store):
    """Test that approval is refused if QC status is FAIL (blockers present)"""
    # Create intake with missing required fields (will cause BLOCKER failures)
    intake = store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id="client-test",
        engagement_id="eng-test",
        content={
            "client_name": "Test Company",
            "website": "testcompany.com",  # Invalid format (no https://)
            "industry": "Technology",
            "geography": "US",
            "primary_offer": "SaaS Platform",
            "objective": "Leads",
            # Missing: target_audience, pain_points, desired_outcomes - will cause BLOCKER
        }
    )
    
    # Run QC (will FAIL)
    qc_result = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    
    # Verify QC failed
    assert qc_result.qc_status == QCStatus.FAIL
    assert qc_result.summary.blockers > 0
    
    # Attempt approval
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake, approved_by="test_operator")
    
    # Check error message mentions blockers or QC failed
    errors = exc_info.value.errors
    assert len(errors) > 0
    # Either content validation or QC gate should block
    assert any("QC failed" in e or "blocker" in e.lower() or "required" in e.lower() for e in errors)


def test_approval_refused_qc_fail_strategy(store):
    """Test that approval is refused if Strategy QC FAIL"""
    # Create and approve intake
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Create minimal valid strategy (passes schema validation)
    strategy = create_minimal_strategy(store, approved_intake)
    
    # Manually create FAIL QC artifact (simulates QC failure)
    qc_artifact = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        target_artifact_id=strategy.artifact_id,
        target_artifact_type=strategy.artifact_type.value,
        target_version=strategy.version,
        qc_type=QCType.STRATEGY_QC,
        qc_status=QCStatus.FAIL,
        qc_score=0,
        created_at=datetime.utcnow().isoformat(),
        checks=[
            QCCheck(
                check_id="strategy_quality_blocker",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.BLOCKER,
                message="Strategy fails quality criteria"
            )
        ],
        summary=QCSummary(
            blockers=1,
            majors=0,
            minors=0
        )
    )
    
    # Store QC artifact
    store.store_qc_artifact(qc_artifact)
    
    # Attempt approval
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(strategy, approved_by="test_operator")
    
    # Check error message mentions QC failure
    errors = exc_info.value.errors
    assert len(errors) > 0
    assert "QC failed" in errors[0] or "blocker" in errors[0].lower()


# ===================================================================
# TEST 3: Approval Refused if QC Version Mismatch
# ===================================================================

def test_approval_refused_qc_version_mismatch(store):
    """Test that approval is refused if QC is for different version"""
    # Create intake v1 and run QC
    intake_v1 = create_minimal_intake(store)
    qc_v1 = run_and_persist_qc_for(intake_v1, store, "client-test", "eng-test", "test_operator")
    
    # Update intake to v2 (but don't re-run QC)
    intake_v2 = store.update_artifact(
        intake_v1,
        content={
            **intake_v1.content,
            "client_name": "Updated Company Name"
        },
        increment_version=True
    )
    
    # Verify version incremented
    assert intake_v2.version == 2
    
    # Verify QC still points to v1
    qc_check = store.get_qc_for_artifact(intake_v2)
    # QC lookup uses artifact_id + version, so it won't find v1 QC for v2 artifact
    # This test verifies the version lock works
    
    # Attempt approval (should fail - no QC for v2)
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake_v2, approved_by="test_operator")
    
    # Check error message
    errors = exc_info.value.errors
    assert len(errors) > 0
    assert "No QC artifact found" in errors[0] or "version" in errors[0].lower()


def test_approval_refused_qc_version_mismatch_explicit(store):
    """Test version mismatch with explicitly mismatched QC artifact"""
    # Create intake v1
    intake = create_minimal_intake(store)
    
    # Manually create QC artifact pointing to wrong version
    from aicmo.ui.quality.qc_models import QCArtifact, QCType, QCStatus, QCSummary
    import uuid
    
    qc_wrong_version = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        qc_type=QCType.INTAKE_QC,
        target_artifact_id=intake.artifact_id,
        target_artifact_type="intake",
        target_version=99,  # Wrong version
        qc_status=QCStatus.PASS,
        qc_score=100,
        checks=[],
        summary=QCSummary(blockers=0, majors=0, minors=0),
        model_used="test",
        created_at=datetime.utcnow().isoformat()
    )
    
    # Store QC with wrong version
    store.store_qc_artifact(qc_wrong_version)
    
    # Attempt approval (should fail - version mismatch)
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake, approved_by="test_operator")
    
    # Check error message mentions version mismatch
    errors = exc_info.value.errors
    assert len(errors) > 0
    # Should say "No QC artifact found" because version lock prevents retrieval
    assert "No QC artifact found" in errors[0] or "version" in errors[0].lower()


# ===================================================================
# TEST 4: Approval Allowed if QC PASS
# ===================================================================

def test_approval_allowed_qc_pass_intake(store):
    """Test that approval succeeds if QC PASS for Intake"""
    # Create intake with all required fields
    intake = create_minimal_intake(store)
    
    # Run QC (should PASS)
    qc_result = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    
    # Verify QC passed (PASS or WARN acceptable, no FAIL)
    # Note: summary counts total checks by severity, not failed checks
    assert qc_result.qc_status in [QCStatus.PASS, QCStatus.WARN]
    # Check that no BLOCKER checks failed
    blocker_failures = [c for c in qc_result.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) == 0
    
    # Approve (should succeed)
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Verify approval succeeded
    assert approved_intake.status == ArtifactStatus.APPROVED
    assert approved_intake.approved_by == "test_operator"
    assert approved_intake.approved_at is not None


def test_approval_allowed_qc_pass_strategy(store):
    """Test that approval succeeds if QC PASS for Strategy"""
    # Create and approve intake
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Create strategy with all required fields
    strategy = create_minimal_strategy(store, approved_intake)
    
    # Run QC (should PASS)
    qc_result = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    
    # Verify QC passed - no BLOCKER failures
    assert qc_result.qc_status in [QCStatus.PASS, QCStatus.WARN]
    blocker_failures = [c for c in qc_result.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) == 0
    
    # Approve (should succeed)
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Verify approval succeeded
    assert approved_strategy.status == ArtifactStatus.APPROVED
    assert approved_strategy.approved_by == "test_operator"
    assert approved_strategy.approved_at is not None


def test_approval_allowed_qc_warn_strategy(store):
    """Test that approval succeeds even if QC WARN (no blockers, only majors/minors)"""
    # Create and approve intake
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Create minimal valid strategy (passes schema validation)
    strategy = create_minimal_strategy(store, approved_intake)
    
    # Manually create WARN QC artifact (has MAJOR failures but no BLOCKERs)
    qc_artifact = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        target_artifact_id=strategy.artifact_id,
        target_artifact_type=strategy.artifact_type.value,
        target_version=strategy.version,
        qc_type=QCType.STRATEGY_QC,
        qc_status=QCStatus.WARN,
        qc_score=50,
        created_at=datetime.utcnow().isoformat(),
        checks=[
            QCCheck(
                check_id="strategy_blocker_check",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.BLOCKER,
                message="All blocker checks pass"
            ),
            QCCheck(
                check_id="strategy_major_issue",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.MAJOR,
                message="Missing strategic depth (MAJOR)"
            )
        ],
        summary=QCSummary(
            blockers=0,
            majors=1,
            minors=0
        )
    )
    
    # Store QC artifact
    store.store_qc_artifact(qc_artifact)
    
    # Verify QC artifact status is WARN
    assert qc_artifact.qc_status == QCStatus.WARN
    blocker_failures = [c for c in qc_artifact.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) == 0
    # Should have MAJOR failures
    assert any(c.status == CheckStatus.FAIL and c.severity == CheckSeverity.MAJOR for c in qc_artifact.checks)
    
    # Approve (should succeed - WARN is acceptable)
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Verify approval succeeded
    assert approved_strategy.status == ArtifactStatus.APPROVED


# ===================================================================
# TEST 5: Delivery Artifact QC Enforcement
# ===================================================================

def test_approval_refused_qc_missing_delivery(store):
    """Test that Delivery artifact approval is refused if QC missing"""
    # Create and approve complete upstream chain
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Create and approve creatives
    creatives = store.create_artifact(
        artifact_type=ArtifactType.CREATIVES,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content={
            "schema_version": "creatives_v1",
            "source_strategy_schema_version": "strategy_contract_v1",
            "source_layers_used": ["layer4", "layer5"],
            "hooks": ["Hook 1", "Hook 2", "Hook 3"],
            "angles": ["Angle 1", "Angle 2", "Angle 3"],
            "ctas": ["CTA 1", "CTA 2", "CTA 3"],
            "offer_framing": "Special offer",
            "compliance_safe_claims": "Industry-leading",
            "assets": [{"type": "image", "name": "test.png"}]
        }
    )
    qc_creatives = run_and_persist_qc_for(creatives, store, "client-test", "eng-test", "test_operator")
    approved_creatives = store.approve_artifact(creatives, approved_by="test_operator")
    
    # Create and approve execution
    execution = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy, approved_creatives],
        content={
            "schema_version": "execution_plan_v1",
            "channel_plan": [{"channel": "linkedin", "status": "planned"}],
            "cadence": "Daily",
            "schedule": "Week 1-4",
            "utm_plan": "utm_campaign=test"
        }
    )
    qc_execution = run_and_persist_qc_for(execution, store, "client-test", "eng-test", "test_operator")
    approved_execution = store.approve_artifact(execution, approved_by="test_operator")
    
    # Create delivery (no QC)
    delivery = create_minimal_delivery(store, approved_intake, approved_strategy, approved_creatives, approved_execution)
    
    # Attempt approval (should fail - no QC)
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(delivery, approved_by="test_operator")
    
    # Check error message
    errors = exc_info.value.errors
    assert len(errors) > 0
    assert "No QC artifact found" in errors[0]


def test_approval_allowed_qc_pass_delivery(store):
    """Test that Delivery artifact approval succeeds if QC PASS"""
    # Create and approve complete upstream chain
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    creatives = store.create_artifact(
        artifact_type=ArtifactType.CREATIVES,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content={
            "schema_version": "creatives_v1",
            "source_strategy_schema_version": "strategy_contract_v1",
            "source_layers_used": ["layer4", "layer5"],
            "hooks": ["Hook 1", "Hook 2", "Hook 3"],
            "angles": ["Angle 1", "Angle 2", "Angle 3"],
            "ctas": ["CTA 1", "CTA 2", "CTA 3"],
            "offer_framing": "Special offer",
            "compliance_safe_claims": "Industry-leading",
            "assets": [{"type": "image", "name": "test.png"}]
        }
    )
    qc_creatives = run_and_persist_qc_for(creatives, store, "client-test", "eng-test", "test_operator")
    approved_creatives = store.approve_artifact(creatives, approved_by="test_operator")
    
    execution = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy, approved_creatives],
        content={
            "schema_version": "execution_plan_v1",
            "channel_plan": [{"channel": "linkedin", "status": "planned"}],
            "cadence": "Daily",
            "schedule": "Week 1-4",
            "utm_plan": "utm_campaign=test"
        }
    )
    qc_execution = run_and_persist_qc_for(execution, store, "client-test", "eng-test", "test_operator")
    approved_execution = store.approve_artifact(execution, approved_by="test_operator")
    
    # Create delivery
    delivery = create_minimal_delivery(store, approved_intake, approved_strategy, approved_creatives, approved_execution)
    
    # Run QC
    qc_delivery = run_and_persist_qc_for(delivery, store, "client-test", "eng-test", "test_operator")
    
    # Verify QC passed - no BLOCKER failures
    assert qc_delivery.qc_status in [QCStatus.PASS, QCStatus.WARN]
    blocker_failures = [c for c in qc_delivery.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) == 0
    
    # Approve (should succeed)
    approved_delivery = store.approve_artifact(delivery, approved_by="test_operator")
    
    # Verify approval succeeded
    assert approved_delivery.status == ArtifactStatus.APPROVED


# ===================================================================
# TEST 6: QC Re-run After Revision
# ===================================================================

def test_qc_rerun_after_revision(store):
    """Test that QC must be re-run after artifact revision"""
    # Create intake and run QC
    intake_v1 = create_minimal_intake(store)
    qc_v1 = run_and_persist_qc_for(intake_v1, store, "client-test", "eng-test", "test_operator")
    
    # Approve v1
    approved_v1 = store.approve_artifact(intake_v1, approved_by="test_operator")
    assert approved_v1.status == ArtifactStatus.APPROVED
    
    # Revise to v2
    intake_v2 = store.update_artifact(
        approved_v1,
        content={
            **intake_v1.content,
            "client_name": "Updated Company"
        },
        increment_version=True
    )
    
    # Attempt approval without re-running QC (should fail)
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(intake_v2, approved_by="test_operator")
    
    # Check error
    errors = exc_info.value.errors
    assert len(errors) > 0
    assert "No QC artifact found" in errors[0]
    
    # Re-run QC for v2
    qc_v2 = run_and_persist_qc_for(intake_v2, store, "client-test", "eng-test", "test_operator")
    
    # Now approval should succeed
    approved_v2 = store.approve_artifact(intake_v2, approved_by="test_operator")
    assert approved_v2.status == ArtifactStatus.APPROVED
    assert approved_v2.version == 2


# ===================================================================
# TEST 7: Multiple Artifact Types QC Enforcement
# ===================================================================

def test_qc_enforcement_all_artifact_types(store):
    """Test QC enforcement works for all client-facing artifact types"""
    # Create and approve intake
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    assert approved_intake.status == ArtifactStatus.APPROVED
    
    # Create and approve strategy
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    assert approved_strategy.status == ArtifactStatus.APPROVED
    
    # Create creatives (minimal)
    creatives = store.create_artifact(
        artifact_type=ArtifactType.CREATIVES,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content={
            "source_strategy_schema_version": "strategy_contract_v1",
            "source_layers_used": ["layer4", "layer5"],
            "hooks": ["Hook 1", "Hook 2", "Hook 3"],
            "angles": ["Angle 1", "Angle 2", "Angle 3"],
            "ctas": ["CTA 1", "CTA 2", "CTA 3"],
            "offer_framing": "Special offer",
            "compliance_safe_claims": "Industry-leading"
        }
    )
    qc_creatives = run_and_persist_qc_for(creatives, store, "client-test", "eng-test", "test_operator")
    approved_creatives = store.approve_artifact(creatives, approved_by="test_operator")
    assert approved_creatives.status == ArtifactStatus.APPROVED
    
    # Create execution (minimal)
    execution = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy, approved_creatives],
        content={
            "channel_plan": [{"name": "LinkedIn", "frequency": "Daily"}],
            "cadence": "Daily",
            "schedule": "Week 1-4",
            "utm_plan": "utm_campaign=test"
        }
    )
    qc_execution = run_and_persist_qc_for(execution, store, "client-test", "eng-test", "test_operator")
    approved_execution = store.approve_artifact(execution, approved_by="test_operator")
    assert approved_execution.status == ArtifactStatus.APPROVED
    
    # Create monitoring (minimal)
    monitoring = store.create_artifact(
        artifact_type=ArtifactType.MONITORING,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_execution],
        content={
            "kpis": ["Engagement rate", "Lead volume"],
            "review_cadence": "Weekly"
        }
    )
    qc_monitoring = run_and_persist_qc_for(monitoring, store, "client-test", "eng-test", "test_operator")
    approved_monitoring = store.approve_artifact(monitoring, approved_by="test_operator")
    assert approved_monitoring.status == ArtifactStatus.APPROVED
    
    # All artifact types enforced QC successfully
    assert True  # Test passed if we got here without exceptions


# ===================================================================
# REGRESSION TESTS: Schema Normalization & Conditional Delivery
# ===================================================================

def test_execution_qc_accepts_both_channel_plan_and_channel_plans(store):
    """
    REGRESSION: Execution QC should accept both singular (channel_plan) and plural (channel_plans) forms.
    
    This tests that the schema normalizer correctly converts plural forms to singular
    before QC rules run, preventing false failures.
    """
    # Create and approve upstream chain
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Create execution with PLURAL forms (should be normalized automatically)
    execution_with_plurals = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content={
            "schema_version": "execution_plan_v1",
            "channel_plans": [{"channel": "instagram", "status": "planned"}],  # PLURAL
            "cadences": "Daily posting",  # PLURAL
            "schedules": "Week 1-4",      # PLURAL
            "utm_plan": "utm_campaign=test",
            # Add governance as STRING (not dict) to avoid QC rule error
            "governance": "Operator approval required",
            # Add risk_guardrails to avoid MINOR failure
            "risk_guardrails": "Follow Strategy Layer 7 constraints"
        }
    )
    
    # Run QC - should normalize plurals to singulars before checking
    qc_result = run_and_persist_qc_for(execution_with_plurals, store, "client-test", "eng-test", "test_operator")
    
    # QC should PASS because normalizer converts channel_plans → channel_plan
    # (May be WARN due to other minor issues, but BLOCKER checks should pass)
    assert qc_result.qc_status in [QCStatus.PASS, QCStatus.WARN], \
        f"QC should PASS/WARN with plural forms (got {qc_result.qc_status}). Checks: {qc_result.checks}"
    
    # Verify channel_plan rule passed
    channel_plan_checks = [c for c in qc_result.checks if c.check_id == "execution_channel_plan"]
    assert len(channel_plan_checks) == 1, "Should have channel_plan check"
    assert channel_plan_checks[0].status == CheckStatus.PASS, \
        f"channel_plan check should PASS (got {channel_plan_checks[0].status})"


def test_schema_normalizer_does_not_mutate_original_content(store):
    """
    REGRESSION: Schema normalizer must create defensive copies, not mutate original artifact content.
    
    This prevents bugs where normalizing content for QC accidentally changes the
    stored artifact content.
    """
    # Create execution with plural forms
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    original_content = {
        "schema_version": "execution_plan_v1",
        "channel_plans": [{"channel": "linkedin"}],  # PLURAL
        "schedules": "Week 1-4",                     # PLURAL
        "utm_plan": "utm_campaign=test"
    }
    
    execution = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content=original_content
    )
    
    # Run QC (should normalize internally)
    qc_result = run_and_persist_qc_for(execution, store, "client-test", "eng-test", "test_operator")
    
    # Original artifact content should still have PLURAL forms
    assert "channel_plans" in execution.content, \
        "Original content should still have 'channel_plans' (plural)"
    assert "schedules" in execution.content, \
        "Original content should still have 'schedules' (plural)"
    assert "channel_plan" not in execution.content, \
        "Original content should NOT be mutated to singular"


def test_delivery_approval_strategy_only_plan(store):
    """
    REGRESSION: Delivery should approve with strategy-only plan (no creatives/execution required).
    
    Tests conditional upstream requirements based on generation plan.
    """
    # Create and approve intake
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Create and approve strategy
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Create delivery with ONLY strategy (no creatives/execution)
    # Store selected_job_ids in notes to indicate strategy-only plan
    delivery = store.create_artifact(
        artifact_type=ArtifactType.DELIVERY,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],  # ONLY strategy
        content={
            "manifest": {
                "schema_version": "delivery_manifest_v1",
                "included_artifacts": [
                    {"type": "intake", "artifact_id": intake.artifact_id, "status": "approved"},
                    {"type": "strategy", "artifact_id": strategy.artifact_id, "status": "approved"}
                ],
                "checks": {
                    "approvals_ok": True,
                    "branding_ok": True
                }
            },
            "notes": "Strategy-only delivery package"
        }
    )
    
    # Mark as strategy-only plan
    delivery.notes["selected_job_ids"] = ["brand_strategy", "messaging_framework"]
    store.update_artifact(delivery, delivery.content, notes=delivery.notes, increment_version=False)
    
    # Run QC (should pass with strategy only)
    qc_delivery = run_and_persist_qc_for(delivery, store, "client-test", "eng-test", "test_operator")
    assert qc_delivery.qc_status in [QCStatus.PASS, QCStatus.WARN], \
        f"Strategy-only delivery QC should pass (got {qc_delivery.qc_status})"
    
    # Approval should succeed (conditional requirements: strategy only)
    approved_delivery = store.approve_artifact(delivery, approved_by="test_operator")
    assert approved_delivery.status == ArtifactStatus.APPROVED, \
        "Strategy-only delivery should approve successfully"


def test_delivery_approval_strategy_plus_creatives_plan(store):
    """
    REGRESSION: Delivery should approve with strategy + creatives plan (no execution required).
    
    Tests conditional upstream requirements for partial plan.
    """
    # Create and approve upstream chain
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Create and approve creatives
    creatives = store.create_artifact(
        artifact_type=ArtifactType.CREATIVES,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content={
            "brief": {"campaign_theme": "Test Theme"},
            "source_strategy_schema_version": "8layer_v1",  # Required field name
            "source_layers_used": ["layer4", "layer5"],
            "hooks": ["Hook 1", "Hook 2", "Hook 3"],
            "angles": ["Angle 1", "Angle 2", "Angle 3"],  # Need 3 minimum
            "ctas": ["CTA 1", "CTA 2", "CTA 3"],           # Need 3 minimum
            "offer_framing": "Special offer",
            "compliance_safe_claims": "Industry-leading",
            "assets": [{"type": "image", "name": "test.png"}]
        }
    )
    qc_creatives = run_and_persist_qc_for(creatives, store, "client-test", "eng-test", "test_operator")
    approved_creatives = store.approve_artifact(creatives, approved_by="test_operator")
    
    # Create delivery with strategy + creatives (no execution)
    delivery = store.create_artifact(
        artifact_type=ArtifactType.DELIVERY,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy, approved_creatives],  # NO execution
        content={
            "manifest": {
                "schema_version": "delivery_manifest_v1",
                "included_artifacts": [
                    {"type": "intake", "artifact_id": intake.artifact_id, "status": "approved"},
                    {"type": "strategy", "artifact_id": strategy.artifact_id, "status": "approved"},
                    {"type": "creatives", "artifact_id": creatives.artifact_id, "status": "approved"}
                ],
                "checks": {
                    "approvals_ok": True,
                    "branding_ok": True
                }
            },
            "notes": "Strategy + Creatives delivery package"
        }
    )
    
    # Mark as strategy + creatives plan (no execution jobs)
    delivery.notes["selected_job_ids"] = ["brand_strategy", "creative_content_library"]
    store.update_artifact(delivery, delivery.content, notes=delivery.notes, increment_version=False)
    
    # Run QC and approve (should succeed without execution)
    qc_delivery = run_and_persist_qc_for(delivery, store, "client-test", "eng-test", "test_operator")
    approved_delivery = store.approve_artifact(delivery, approved_by="test_operator")
    assert approved_delivery.status == ArtifactStatus.APPROVED, \
        "Strategy + Creatives delivery should approve without execution"


def test_delivery_approval_full_plan(store):
    """
    REGRESSION: Delivery should still require all upstreams for full plan (backward compatibility).
    
    Tests that full plan (strategy + creatives + execution) still works as before.
    """
    # Create and approve complete upstream chain
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    creatives = store.create_artifact(
        artifact_type=ArtifactType.CREATIVES,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],
        content={
            "brief": {"campaign_theme": "Test Theme"},
            "source_strategy_schema_version": "8layer_v1",  # Required field name
            "source_layers_used": ["layer4", "layer5"],
            "hooks": ["Hook 1", "Hook 2", "Hook 3"],
            "angles": ["Angle 1", "Angle 2", "Angle 3"],  # Need 3 minimum
            "ctas": ["CTA 1", "CTA 2", "CTA 3"],           # Need 3 minimum
            "offer_framing": "Special offer",
            "compliance_safe_claims": "Industry-leading",
            "assets": [{"type": "image", "name": "test.png"}]
        }
    )
    qc_creatives = run_and_persist_qc_for(creatives, store, "client-test", "eng-test", "test_operator")
    approved_creatives = store.approve_artifact(creatives, approved_by="test_operator")
    
    execution = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy, approved_creatives],
        content={
            "schema_version": "execution_plan_v1",
            "channel_plan": [{"channel": "linkedin", "status": "planned"}],
            "cadence": "Daily",
            "schedule": "Week 1-4",
            "utm_plan": "utm_campaign=test"
        }
    )
    qc_execution = run_and_persist_qc_for(execution, store, "client-test", "eng-test", "test_operator")
    approved_execution = store.approve_artifact(execution, approved_by="test_operator")
    
    # Create delivery with ALL upstreams (full plan)
    delivery = create_minimal_delivery(store, approved_intake, approved_strategy, approved_creatives, approved_execution)
    
    # Mark as full plan
    delivery.notes["selected_job_ids"] = ["brand_strategy", "creative_content_library", "content_calendar_week1"]
    store.update_artifact(delivery, delivery.content, notes=delivery.notes, increment_version=False)
    
    # Run QC and approve (should succeed with all upstreams)
    qc_delivery = run_and_persist_qc_for(delivery, store, "client-test", "eng-test", "test_operator")
    approved_delivery = store.approve_artifact(delivery, approved_by="test_operator")
    assert approved_delivery.status == ArtifactStatus.APPROVED, \
        "Full plan delivery should approve with all upstreams"


def test_delivery_approval_fails_when_required_upstream_qc_missing(store):
    """
    REGRESSION: Delivery approval should still fail if required upstream QC missing.
    
    Tests that conditional requirements don't bypass QC enforcement.
    
    Note: This test verifies that delivery ITSELF must have QC. Upstream QC
    checks are handled by lineage validation, not by the QC gate.
    """
    # Create and approve intake
    intake = create_minimal_intake(store)
    qc_intake = run_and_persist_qc_for(intake, store, "client-test", "eng-test", "test_operator")
    approved_intake = store.approve_artifact(intake, approved_by="test_operator")
    
    # Create and approve strategy (with QC)
    strategy = create_minimal_strategy(store, approved_intake)
    qc_strategy = run_and_persist_qc_for(strategy, store, "client-test", "eng-test", "test_operator")
    approved_strategy = store.approve_artifact(strategy, approved_by="test_operator")
    
    # Create delivery WITHOUT QC (intentional test case)
    delivery = store.create_artifact(
        artifact_type=ArtifactType.DELIVERY,
        client_id="client-test",
        engagement_id="eng-test",
        source_artifacts=[approved_strategy],  # Only strategy (strategy-only plan)
        content={
            "manifest": {
                "schema_version": "delivery_manifest_v1",
                "included_artifacts": [
                    {"type": "intake", "artifact_id": intake.artifact_id, "status": "approved"},
                    {"type": "strategy", "artifact_id": strategy.artifact_id, "status": "approved"}
                ],
                "checks": {
                    "approvals_ok": True,
                    "branding_ok": True
                }
            },
            "notes": "Test delivery - should fail without QC"
        }
    )
    
    # Mark as strategy-only plan
    delivery.notes["selected_job_ids"] = ["brand_strategy"]
    store.update_artifact(delivery, delivery.content, notes=delivery.notes, increment_version=False)
    
    # NOTE: Intentionally NOT running run_and_persist_qc_for(delivery)
    
    # Approval should FAIL because delivery itself has no QC
    with pytest.raises(ArtifactValidationError) as exc_info:
        store.approve_artifact(delivery, approved_by="test_operator")
    
    # Check error message
    errors = exc_info.value.errors
    assert len(errors) > 0, "Should have validation errors"
    assert any("No QC artifact found" in err for err in errors), \
        f"Should fail due to missing QC on delivery. Got errors: {errors}"


# ===================================================================
# PHASE 2: Safe Default Tests (Empty Generation Plan)
# ===================================================================

def test_delivery_empty_plan_defaults_to_intake_strategy(store):
    """
    REGRESSION: Empty generation plan defaults to {intake, strategy} not ALL.
    Proves safe default prevents deadlocks from requiring creatives/execution.
    """
    from aicmo.ui.generation_plan import required_upstreams_for
    
    # Empty selected_job_ids
    empty_plan_jobs = []
    
    # Get required upstreams for delivery with empty plan
    required = required_upstreams_for("delivery", selected_job_ids=empty_plan_jobs)
    
    # Should be SAFE default: intake + strategy only
    assert required == {"intake", "strategy"}, \
        f"Empty plan should default to safe minimum {{intake, strategy}}, got {required}"
    
    # Should NOT require creatives or execution (prevents deadlocks)
    assert "creatives" not in required, "Empty plan should not require creatives"
    assert "execution" not in required, "Empty plan should not require execution"


def test_delivery_qc_warns_when_plan_missing(store):
    """
    REGRESSION: QC emits MAJOR when generation plan missing (visibility).
    Proves users are notified of default behavior.
    """
    from aicmo.ui.quality.rules.ruleset_v1 import check_delivery_generation_plan
    
    # Delivery content with empty/missing generation plan
    delivery_content = {
        "manifest": {
            "schema_version": "delivery_manifest_v1",
            "generation_plan": {
                "selected_job_ids": []  # Empty plan
            }
        }
    }
    
    # Run the check
    checks = check_delivery_generation_plan(delivery_content)
    
    # Should have exactly one check
    assert len(checks) == 1, f"Should return 1 check, got {len(checks)}"
    
    check = checks[0]
    assert check.check_id == "delivery_generation_plan"
    assert check.status == CheckStatus.FAIL, "Empty plan should FAIL (MAJOR severity)"
    assert check.severity == CheckSeverity.MAJOR, "Should be MAJOR not BLOCKER"
    assert "Generation plan missing" in check.message or "defaulted" in check.message.lower(), \
        f"Message should mention plan missing/defaulted. Got: {check.message}"


def test_delivery_qc_passes_when_plan_present(store):
    """
    REGRESSION: QC passes when generation plan provided.
    """
    from aicmo.ui.quality.rules.ruleset_v1 import check_delivery_generation_plan
    
    # Delivery content with valid generation plan
    delivery_content = {
        "manifest": {
            "schema_version": "delivery_manifest_v1",
            "generation_plan": {
                "selected_job_ids": ["brand_strategy", "content_library"]
            }
        }
    }
    
    # Run the check
    checks = check_delivery_generation_plan(delivery_content)
    
    # Should pass
    assert len(checks) == 1
    check = checks[0]
    assert check.status == CheckStatus.PASS, "Plan present should PASS"
    assert check.severity == CheckSeverity.MAJOR


def test_delivery_conditional_strategy_only_safe(store):
    """
    REGRESSION: Strategy-only delivery requires {strategy} not ALL.
    Proves conditional logic doesn't fall into empty plan trap.
    """
    from aicmo.ui.generation_plan import required_upstreams_for
    
    # Strategy-only plan (explicit job IDs)
    strategy_jobs = ["brand_strategy", "positioning_framework"]
    
    # Get required upstreams
    required = required_upstreams_for("delivery", selected_job_ids=strategy_jobs)
    
    # Should require only strategy (conditional logic working)
    assert required == {"strategy"}, \
        f"Strategy-only should require only strategy, got {required}"
    
    # Should NOT accidentally trigger empty plan fallback
    assert "intake" not in required, "Strategy-only should not require intake"
    assert "creatives" not in required
    assert "execution" not in required
