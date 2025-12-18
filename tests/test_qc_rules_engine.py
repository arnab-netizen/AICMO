"""
Unit Tests for QC Rules Engine

Tests deterministic rules, enforcement logic, and persistence.
"""
import pytest
from aicmo.ui.persistence.artifact_store import (
    ArtifactStore,
    Artifact,
    ArtifactType,
    ArtifactStatus
)
from aicmo.ui.quality.qc_models import (
    QCArtifact,
    QCStatus,
    CheckStatus,
    CheckSeverity
)
from aicmo.ui.quality.rules import (
    run_qc_for_artifact,
    has_blocking_failures,
    get_blocking_checks,
    save_qc_result,
    load_latest_qc
)


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


# ===================================================================
# Test 1: Intake Missing Required Fields -> BLOCKER Fail
# ===================================================================

def test_intake_missing_required_fields_blocker_fail(store):
    """Test that intake with missing required fields fails with BLOCKER"""
    # Create intake artifact with missing fields
    intake = Artifact(
        artifact_id="intake-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "client_name": "Test Company",
            "website": "",  # Missing
            "industry": "Technology",
            # Missing: geography, primary_offer, target_audience, pain_points, desired_outcomes
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, intake)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    assert qc_result.summary.blockers > 0
    
    # Check for specific BLOCKER failures
    blocker_failures = [c for c in qc_result.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) > 0
    
    # Should fail required fields check
    required_fields_check = [c for c in qc_result.checks if c.check_id == "intake_required_fields"]
    assert len(required_fields_check) == 1
    assert required_fields_check[0].status == CheckStatus.FAIL


# ===================================================================
# Test 2: Intake Valid Minimal -> PASS or Only MINOR
# ===================================================================

def test_intake_valid_minimal_pass(store):
    """Test that intake with all required fields passes (or only has MINOR failures)"""
    intake = Artifact(
        artifact_id="intake-124",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "client_name": "Test Company",
            "website": "testcompany.com",
            "industry": "Technology",
            "geography": "US",
            "primary_offer": "SaaS Platform",
            "target_audience": "B2B SaaS Companies",
            "pain_points": "Manual processes, high costs",
            "desired_outcomes": "Reduce costs by 30%",
            "compliance_requirements": "GDPR compliant",
            "proof_assets": "3 case studies available",
            "pricing_logic": "Tiered pricing $99-$499/mo",
            # Missing: brand_voice (MINOR)
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, intake)
    
    # Assertions: Should not have BLOCKER failures
    blocker_failures = [c for c in qc_result.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) == 0
    
    # Status should be PASS or WARN (not FAIL)
    assert qc_result.qc_status in [QCStatus.PASS, QCStatus.WARN]


# ===================================================================
# Test 3: Strategy Wrong Schema Version -> BLOCKER Fail
# ===================================================================

def test_strategy_wrong_schema_version_blocker_fail(store):
    """Test that strategy with wrong schema version fails with BLOCKER"""
    strategy = Artifact(
        artifact_id="strategy-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.STRATEGY,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "schema_version": "strategy_v2",  # Wrong version
            "layer1_business_reality": {},
            # ...
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, strategy)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Check for schema version failure
    schema_check = [c for c in qc_result.checks if c.check_id == "strategy_schema_version"]
    assert len(schema_check) == 1
    assert schema_check[0].status == CheckStatus.FAIL
    assert schema_check[0].severity == CheckSeverity.BLOCKER


# ===================================================================
# Test 4: Strategy Missing a Layer -> BLOCKER Fail
# ===================================================================

def test_strategy_missing_layer_blocker_fail(store):
    """Test that strategy missing a layer fails with BLOCKER"""
    strategy = Artifact(
        artifact_id="strategy-124",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.STRATEGY,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "schema_version": "strategy_contract_v1",
            "layer1_business_reality": {},
            "layer2_market_truth": {},
            # Missing: layer3, layer4, layer5, layer6, layer7, layer8
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, strategy)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Check for missing layers failure
    layers_check = [c for c in qc_result.checks if c.check_id == "strategy_all_layers"]
    assert len(layers_check) == 1
    assert layers_check[0].status == CheckStatus.FAIL
    assert layers_check[0].severity == CheckSeverity.BLOCKER


# ===================================================================
# Test 5: Strategy Minimal Valid -> PASS (No BLOCKER)
# ===================================================================

def test_strategy_minimal_valid_pass(store):
    """Test that strategy with all required fields passes"""
    strategy = Artifact(
        artifact_id="strategy-125",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.STRATEGY,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "schema_version": "strategy_contract_v1",
            "layer1_business_reality": {
                "business_model_summary": "B2B SaaS",
                "revenue_streams": "Subscriptions",
                "unit_economics": "CAC $500, LTV $5000"
            },
            "layer2_market_truth": {
                "category_maturity": "Growth",
                "white_space_logic": "Mid-market underserved",
                "what_not_to_do": "Don't compete on price"
            },
            "layer3_audience_psychology": {
                "awareness_state": "Problem-aware",
                "objection_hierarchy": "Price, implementation"
            },
            "layer4_value_architecture": {
                "core_promise": "Reduce costs 30%",
                "differentiation_logic": "Structural"
            },
            "layer5_narrative": {
                "narrative_problem": "Manual processes",
                "narrative_resolution": "Automation",
                "enemy_definition": "Manual work",
                "repetition_logic": "Automation saves time and reduces errors"
            },
            "layer6_channel_strategy": {
                "channels": [
                    {"name": "LinkedIn", "strategic_role": "Awareness"}
                ]
            },
            "layer7_constraints": {
                "tone_boundaries": "Professional",
                "forbidden_language": "No hype"
            },
            "layer8_measurement": {
                "success_definition": "100 leads/month",
                "leading_indicators": "Engagement rate",
                "lagging_indicators": "Lead volume"
            }
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, strategy)
    
    # Assertions: Should not have BLOCKER failures
    blocker_failures = [c for c in qc_result.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) == 0


# ===================================================================
# Test 6: Creatives Missing Hooks/Angles/CTAs -> BLOCKER Fail
# ===================================================================

def test_creatives_missing_assets_blocker_fail(store):
    """Test that creatives with insufficient assets fails with BLOCKER"""
    creatives = Artifact(
        artifact_id="creatives-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.CREATIVES,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "source_strategy_schema_version": "strategy_contract_v1",
            "source_layers_used": ["layer4", "layer5"],
            "hooks": ["Hook 1"],  # Need 3
            "angles": [],  # Need 3
            "ctas": ["CTA 1", "CTA 2"],  # Need 3
            "offer_framing": "Special offer",
            "compliance_safe_claims": "Industry-leading"
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, creatives)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Check for minimum assets failure
    assets_check = [c for c in qc_result.checks if c.check_id == "creatives_minimum_assets"]
    assert len(assets_check) == 1
    assert assets_check[0].status == CheckStatus.FAIL
    assert assets_check[0].severity == CheckSeverity.BLOCKER


# ===================================================================
# Test 7: Execution Missing Channel Plan -> BLOCKER Fail
# ===================================================================

def test_execution_missing_channel_plan_blocker_fail(store):
    """Test that execution without channel plan fails with BLOCKER"""
    execution = Artifact(
        artifact_id="execution-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.EXECUTION,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "channel_plan": [],  # Empty
            "cadence": "Daily",
            "schedule": "Week 1-4",
            "utm_plan": "utm_campaign=test"
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, execution)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Check for channel plan failure
    channel_check = [c for c in qc_result.checks if c.check_id == "execution_channel_plan"]
    assert len(channel_check) == 1
    assert channel_check[0].status == CheckStatus.FAIL
    assert channel_check[0].severity == CheckSeverity.BLOCKER


# ===================================================================
# Test 8: Monitoring Missing KPIs -> BLOCKER Fail
# ===================================================================

def test_monitoring_missing_kpis_blocker_fail(store):
    """Test that monitoring without KPIs fails with BLOCKER"""
    monitoring = Artifact(
        artifact_id="monitoring-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.MONITORING,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "kpis": [],  # Empty
            "review_cadence": "Weekly"
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, monitoring)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Check for KPIs failure
    kpis_check = [c for c in qc_result.checks if c.check_id == "monitoring_kpis"]
    assert len(kpis_check) == 1
    assert kpis_check[0].status == CheckStatus.FAIL
    assert kpis_check[0].severity == CheckSeverity.BLOCKER


# ===================================================================
# Test 9: Delivery Manifest approvals_ok False -> BLOCKER Fail
# ===================================================================

def test_delivery_approvals_not_ok_blocker_fail(store):
    """Test that delivery with approvals_ok=false fails with BLOCKER"""
    delivery = Artifact(
        artifact_id="delivery-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.DELIVERY,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "manifest": {
                "schema_version": "delivery_manifest_v1",
                "included_artifacts": [
                    {"type": "intake", "status": "approved"},
                    {"type": "strategy", "status": "draft"}  # Not approved
                ],
                "checks": {
                    "approvals_ok": False,  # BLOCKER
                    "branding_ok": True
                }
            }
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, delivery)
    
    # Assertions
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Check for approvals failure
    approvals_check = [c for c in qc_result.checks if c.check_id == "delivery_approvals_ok"]
    assert len(approvals_check) == 1
    assert approvals_check[0].status == CheckStatus.FAIL
    assert approvals_check[0].severity == CheckSeverity.BLOCKER


# ===================================================================
# Test 10: QC Persistence Saves and Loads Latest
# ===================================================================

def test_qc_persistence_saves_and_loads(store):
    """Test that QC results can be saved and loaded"""
    intake = Artifact(
        artifact_id="intake-126",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "client_name": "Test",
            "website": "test.com",
            "industry": "Tech",
            "geography": "US",
            "primary_offer": "Product",
            "target_audience": "SMBs",
            "pain_points": "High costs",
            "desired_outcomes": "Save money",
            "compliance_requirements": "None"
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, intake)
    
    # Save
    save_qc_result(store, qc_result, "client-123", "eng-123", "intake-126")
    
    # Load
    loaded_qc = load_latest_qc(store, "intake", "eng-123")
    
    # Assertions
    assert loaded_qc is not None
    assert loaded_qc.target_artifact_id == "intake-126"
    assert loaded_qc.qc_status == qc_result.qc_status
    assert len(loaded_qc.checks) == len(qc_result.checks)


# ===================================================================
# Test 11: Approve Enforcement - Blocker Disables Approve
# ===================================================================

def test_can_approve_artifact_blocker_prevents(store):
    """Test enforcement helper: BLOCKER prevents approval"""
    # Create artifact with missing fields
    intake = Artifact(
        artifact_id="intake-127",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "client_name": "Test",
            # Missing required fields
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, intake)
    
    # Check blocking failures
    has_blockers = has_blocking_failures(qc_result)
    assert has_blockers is True
    
    # Get blocking checks
    blockers = get_blocking_checks(qc_result)
    assert len(blockers) > 0


# ===================================================================
# Test 12: Delivery Generation Enforcement - Blocked if Artifact Has Blocker
# ===================================================================

def test_delivery_generation_blocked_by_artifact_qc(store):
    """Test that delivery generation is blocked if selected artifact has BLOCKER failures"""
    # Create strategy with missing layer
    strategy = Artifact(
        artifact_id="strategy-127",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.STRATEGY,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "schema_version": "strategy_contract_v1",
            "layer1_business_reality": {},
            # Missing other layers
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, strategy)
    
    # Save QC result
    save_qc_result(store, qc_result, "client-123", "eng-123", "strategy-127")
    
    # Check if this would block delivery
    has_blockers = has_blocking_failures(qc_result)
    assert has_blockers is True
    
    # Simulate delivery check
    # If strategy is selected for delivery, check its QC
    strategy_qc = load_latest_qc(store, "strategy", "eng-123")
    assert strategy_qc is not None
    
    delivery_blocked = has_blocking_failures(strategy_qc)
    assert delivery_blocked is True


# ===================================================================
# Test 13: QC Status Computation - FAIL if Any BLOCKER Fails
# ===================================================================

def test_qc_status_computation_fail_on_blocker(store):
    """Test that QC status is FAIL if any BLOCKER check fails"""
    intake = Artifact(
        artifact_id="intake-128",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "client_name": "",  # Empty - should fail
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, intake)
    
    # Should be FAIL
    assert qc_result.qc_status == QCStatus.FAIL
    
    # Should have BLOCKER failures
    blocker_failures = [c for c in qc_result.checks if c.severity == CheckSeverity.BLOCKER and c.status == CheckStatus.FAIL]
    assert len(blocker_failures) > 0


# ===================================================================
# Test 14: QC Score Computation - Penalty for Failures
# ===================================================================

def test_qc_score_computation_penalty(store):
    """Test that QC score is penalized for failures"""
    intake = Artifact(
        artifact_id="intake-129",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.DRAFT,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        content={
            "client_name": "",  # Will cause BLOCKER failure (-30 points)
        }
    )
    
    # Run QC
    qc_result = run_qc_for_artifact(store, intake)
    
    # Score should be less than 100
    assert qc_result.qc_score < 100
    
    # Score should be >= 0
    assert qc_result.qc_score >= 0
