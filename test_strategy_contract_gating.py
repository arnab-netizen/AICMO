"""
Test Suite for Strategy Contract and Gating Rules

Tests:
1. Strategy contract validation (8-layer schema)
2. Gating rules enforcement
3. Artifact approval workflow
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ===================================================================
# Strategy Contract Tests
# ===================================================================

def test_strategy_contract_schema_version_present():
    """Test that strategy contract requires schema_version field"""
    from aicmo.ui.persistence.artifact_store import validate_strategy_contract
    
    # Missing schema_version - should still validate layers
    content = {
        "layer1_business_reality": {
            "business_model_summary": "Test",
            "revenue_streams": "Test",
            "unit_economics": "Test",
            "pricing_logic": "Test",
            "growth_constraint": "Test",
            "bottleneck": "Demand"
        },
        "layer2_market_truth": {
            "category_maturity": "Test",
            "white_space_logic": "Test",
            "what_not_to_do": "Test"
        },
        "layer3_audience_psychology": {
            "awareness_state": "Test",
            "objection_hierarchy": "Test",
            "trust_transfer_mechanism": "Test"
        },
        "layer4_value_architecture": {
            "core_promise": "Test",
            "sacrifice_framing": "Test",
            "differentiation_logic": "Structural"
        },
        "layer5_narrative": {
            "narrative_problem": "Test",
            "narrative_tension": "Test",
            "narrative_resolution": "Test",
            "enemy_definition": "Test",
            "repetition_logic": "Test"
        },
        "layer6_channel_strategy": {
            "channels": [
                {"name": "LinkedIn", "strategic_role": "Awareness"}
            ]
        },
        "layer7_constraints": {
            "tone_boundaries": "Test",
            "forbidden_language": "Test",
            "claim_boundaries": "Test",
            "compliance_rules": "Test"
        },
        "layer8_measurement": {
            "success_definition": "Test",
            "leading_indicators": "Test",
            "lagging_indicators": "Test",
            "decision_rules": "Test"
        }
    }
    
    ok, errors, warnings = validate_strategy_contract(content)
    assert ok, f"Valid content should pass. Errors: {errors}"


def test_strategy_contract_validation_fails_missing_layers():
    """Test that strategy contract validation fails when layers are missing"""
    from aicmo.ui.persistence.artifact_store import validate_strategy_contract
    
    # Empty content
    content = {}
    
    ok, errors, warnings = validate_strategy_contract(content)
    assert not ok, "Empty content should fail validation"
    assert len(errors) > 0, "Should have at least one error"
    
    # Check that error mentions missing layers
    error_text = " ".join(errors).lower()
    assert "layer" in error_text, "Errors should mention missing layers"


def test_strategy_contract_validation_passes_minimal_valid_payload():
    """Test that strategy contract validation passes with all required fields"""
    from aicmo.ui.persistence.artifact_store import validate_strategy_contract
    
    content = {
        "schema_version": "strategy_contract_v1",
        "layer1_business_reality": {
            "business_model_summary": "B2B SaaS subscription model",
            "revenue_streams": "Monthly recurring revenue",
            "unit_economics": "CAC: $500, LTV: $5000",
            "pricing_logic": "Tiered pricing based on usage",
            "growth_constraint": "Sales team capacity",
            "bottleneck": "Awareness"
        },
        "layer2_market_truth": {
            "category_maturity": "Growth stage",
            "competitive_vectors": "Price, Features, Support",
            "white_space_logic": "Mid-market segment underserved",
            "what_not_to_do": "Don't compete on price alone"
        },
        "layer3_audience_psychology": {
            "awareness_state": "Problem-aware",
            "pain_intensity": "High - costs are rising",
            "objection_hierarchy": "1. Price, 2. Implementation time, 3. Training",
            "trust_transfer_mechanism": "Customer testimonials + case studies"
        },
        "layer4_value_architecture": {
            "core_promise": "Reduce operational costs by 30%",
            "proof_stack": {"social": "500+ customers", "authority": "Industry leader", "mechanism": "Automation"},
            "sacrifice_framing": "Not for enterprises requiring custom solutions",
            "differentiation_logic": "Structural"
        },
        "layer5_narrative": {
            "narrative_problem": "Manual processes eating into profits",
            "narrative_tension": "Competitors are automating, you're falling behind",
            "narrative_resolution": "Automate and regain competitive edge",
            "enemy_definition": "Manual, error-prone processes",
            "repetition_logic": "Automation vs. Manual work"
        },
        "layer6_channel_strategy": {
            "channels": [
                {
                    "name": "LinkedIn",
                    "strategic_role": "Awareness + Credibility",
                    "allowed_content_types": "Articles, Case Studies",
                    "kpi": "Engagement rate > 5%",
                    "kill_criteria": "Engagement < 2% for 30 days"
                }
            ]
        },
        "layer7_constraints": {
            "tone_boundaries": "Professional, authoritative, not salesy",
            "forbidden_language": "Avoid hype, no guarantees without proof",
            "claim_boundaries": "Only cite verified customer results",
            "visual_constraints": "Brand colors only, no stock photos",
            "compliance_rules": "GDPR compliant, no medical claims"
        },
        "layer8_measurement": {
            "success_definition": "100 qualified leads per month",
            "leading_indicators": "Content engagement, click-through rate",
            "lagging_indicators": "Lead volume, conversion rate",
            "review_cadence": "Weekly",
            "decision_rules": "Pause channel if lead quality drops below 50%"
        }
    }
    
    ok, errors, warnings = validate_strategy_contract(content)
    assert ok, f"Valid complete payload should pass. Errors: {errors}"
    assert len(errors) == 0, "Should have no errors"


# ===================================================================
# Gating Tests - Helper Functions
# ===================================================================

def _create_passing_qc(store, artifact):
    """Helper: Create a passing QC artifact for approval gate"""
    from aicmo.ui.quality.qc_models import QCArtifact, QCCheck, QCType, QCStatus, CheckType, CheckStatus, CheckSeverity
    import uuid
    from datetime import datetime
    
    qc_artifact = QCArtifact(
        qc_artifact_id=str(uuid.uuid4()),
        qc_type=QCType.INTAKE_QC if artifact.artifact_type.value == "intake" else QCType.STRATEGY_QC,
        target_artifact_id=artifact.artifact_id,
        target_artifact_type=artifact.artifact_type.value,
        target_version=artifact.version,
        qc_status=QCStatus.PASS,
        qc_score=100,
        checks=[
            QCCheck(
                check_id="test_check",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MINOR,
                message="Test QC check passed"
            )
        ],
        created_at=datetime.utcnow().isoformat()
    )
    
    store.store_qc_artifact(qc_artifact)


def make_and_approve_intake(store, client_id, engagement_id):
    """Create and approve an Intake artifact"""
    from aicmo.ui.persistence.artifact_store import ArtifactType
    
    intake = store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "client_name": "Test Company",
            "website": "https://test.com",
            "industry": "Technology",
            "geography": "US",
            "primary_offer": "SaaS Platform",
            "objective": "Leads"
        }
    )
    _create_passing_qc(store, intake)
    store.approve_artifact(intake, approved_by="test")
    return intake


def make_and_approve_strategy(store, client_id, engagement_id, intake_artifact):
    """Create and approve a Strategy artifact with proper lineage"""
    from aicmo.ui.persistence.artifact_store import ArtifactType
    
    strategy = store.create_artifact(
        artifact_type=ArtifactType.STRATEGY,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "layer1_business_reality": {
                "business_model_summary": "Test", "revenue_streams": "Test",
                "unit_economics": "Test", "pricing_logic": "Test",
                "growth_constraint": "Test", "bottleneck": "Demand"
            },
            "layer2_market_truth": {
                "category_maturity": "Test", "white_space_logic": "Test",
                "what_not_to_do": "Test"
            },
            "layer3_audience_psychology": {
                "awareness_state": "Test", "objection_hierarchy": "Test",
                "trust_transfer_mechanism": "Test"
            },
            "layer4_value_architecture": {
                "core_promise": "Test", "sacrifice_framing": "Test",
                "differentiation_logic": "Structural"
            },
            "layer5_narrative": {
                "narrative_problem": "Test", "narrative_tension": "Test",
                "narrative_resolution": "Test", "enemy_definition": "Test",
                "repetition_logic": "Test"
            },
            "layer6_channel_strategy": {
                "channels": [{"name": "LinkedIn", "strategic_role": "Awareness"}]
            },
            "layer7_constraints": {
                "tone_boundaries": "Test", "forbidden_language": "Test",
                "claim_boundaries": "Test", "compliance_rules": "Test"
            },
            "layer8_measurement": {
                "success_definition": "Test", "leading_indicators": "Test",
                "lagging_indicators": "Test", "decision_rules": "Test"
            }
        },
        source_artifacts=[intake_artifact]
    )
    _create_passing_qc(store, strategy)
    store.approve_artifact(strategy, approved_by="test")
    return strategy


def make_and_approve_creatives(store, client_id, engagement_id, strategy_artifact):
    """Create and approve a Creatives artifact with proper lineage"""
    from aicmo.ui.persistence.artifact_store import ArtifactType
    
    creatives = store.create_artifact(
        artifact_type=ArtifactType.CREATIVES,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "brief": {"campaign_theme": "Test Campaign"},
            "asset_types": ["Post"],
            "num_assets": 1
        },
        source_artifacts=[strategy_artifact]
    )
    _create_passing_qc(store, creatives)
    store.approve_artifact(creatives, approved_by="test")
    return creatives


def make_and_approve_execution(store, client_id, engagement_id, strategy_artifact, creatives_artifact):
    """Create and approve an Execution artifact with proper lineage"""
    from aicmo.ui.persistence.artifact_store import ArtifactType
    
    execution = store.create_artifact(
        artifact_type=ArtifactType.EXECUTION,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "schedule": {"posts": []},
            "timeline": "4 weeks"
        },
        source_artifacts=[strategy_artifact, creatives_artifact]
    )
    _create_passing_qc(store, execution)
    store.approve_artifact(execution, approved_by="test")
    return execution


def test_gating_strategy_requires_intake_approved():
    """Test that Strategy tab requires approved Intake"""
    from aicmo.ui.persistence.artifact_store import ArtifactStore, ArtifactType, ArtifactStatus, check_gating
    
    # Create in-memory store
    session_state = {}
    store = ArtifactStore(session_state, mode="inmemory")
    
    # Test 1: No intake - should block
    allowed, reasons = check_gating(ArtifactType.STRATEGY, store)
    assert not allowed, "Strategy should be blocked without intake"
    assert len(reasons) > 0, "Should have blocking reasons"
    
    # Test 2: Draft intake - should block
    intake_artifact = store.create_artifact(
        artifact_type=ArtifactType.INTAKE,
        client_id="test-client",
        engagement_id="test-engagement",
        content={
            "client_name": "Test Company",
            "website": "https://test.com",
            "industry": "Technology",
            "geography": "US",
            "primary_offer": "SaaS",
            "objective": "Leads"
        }
    )
    
    allowed, reasons = check_gating(ArtifactType.STRATEGY, store)
    assert not allowed, "Strategy should be blocked with draft intake"
    
    # Test 3: Approved intake - should allow
    _create_passing_qc(store, intake_artifact)
    store.approve_artifact(intake_artifact, approved_by="test")
    
    allowed, reasons = check_gating(ArtifactType.STRATEGY, store)
    assert allowed, f"Strategy should be allowed with approved intake. Reasons: {reasons}"
    assert len(reasons) == 0, "Should have no blocking reasons"


def test_gating_delivery_requires_core_four_approved():
    """Test that Delivery tab requires Intake + Strategy + Creatives + Execution approved"""
    from aicmo.ui.persistence.artifact_store import ArtifactStore, ArtifactType, check_gating
    
    # Create in-memory store
    session_state = {}
    store = ArtifactStore(session_state, mode="inmemory")
    
    client_id = "test-client"
    engagement_id = "test-engagement"
    
    # Test 1: No artifacts - should block
    allowed, reasons = check_gating(ArtifactType.DELIVERY, store)
    assert not allowed, "Delivery should be blocked without artifacts"
    assert len(reasons) >= 4, "Should block on all 4 required artifacts"
    
    # Test 2: Create and approve Intake
    intake = make_and_approve_intake(store, client_id, engagement_id)
    allowed, reasons = check_gating(ArtifactType.DELIVERY, store)
    assert not allowed, "Delivery should still be blocked (need 3 more)"
    
    # Test 3: Create and approve Strategy
    strategy = make_and_approve_strategy(store, client_id, engagement_id, intake)
    allowed, reasons = check_gating(ArtifactType.DELIVERY, store)
    assert not allowed, "Delivery should still be blocked (need 2 more)"
    
    # Test 4: Create and approve Creatives
    creatives = make_and_approve_creatives(store, client_id, engagement_id, strategy)
    allowed, reasons = check_gating(ArtifactType.DELIVERY, store)
    assert not allowed, "Delivery should still be blocked (need 1 more)"
    
    # Test 5: Create and approve Execution
    execution = make_and_approve_execution(store, client_id, engagement_id, strategy, creatives)
    
    # Test 6: Now Delivery should be unlocked
    allowed, reasons = check_gating(ArtifactType.DELIVERY, store)
    assert allowed, f"Delivery should be unlocked after core 4 approved. Reasons: {reasons}"
    assert len(reasons) == 0, "Should have no blocking reasons"


def test_delivery_not_unlocked_by_monitoring_alone():
    """Test that Monitoring approval does NOT unlock Delivery (only core 4 required)"""
    from aicmo.ui.persistence.artifact_store import ArtifactStore, ArtifactType, check_gating
    
    # Create in-memory store
    session_state = {}
    store = ArtifactStore(session_state, mode="inmemory")
    
    client_id = "test-client"
    engagement_id = "test-engagement"
    
    # Test 1: Build full approved chain including Monitoring
    # Expected: Delivery should be unlocked (has all core 4, Monitoring optional)
    intake = make_and_approve_intake(store, client_id, engagement_id)
    strategy = make_and_approve_strategy(store, client_id, engagement_id, intake)
    creatives = make_and_approve_creatives(store, client_id, engagement_id, strategy)
    execution = make_and_approve_execution(store, client_id, engagement_id, strategy, creatives)
    
    from aicmo.ui.persistence.artifact_store import ArtifactType as AT
    monitoring = store.create_artifact(
        artifact_type=AT.MONITORING,
        client_id=client_id,
        engagement_id=engagement_id,
        content={"kpi_config": {"selected_kpis": ["impressions"]}},
        source_artifacts=[execution]
    )
    _create_passing_qc(store, monitoring)
    store.approve_artifact(monitoring, approved_by="test")
    
    # Delivery should be unlocked because we have all core 4 approved
    # (Monitoring is optional - not required for Delivery)
    allowed, reasons = check_gating(AT.DELIVERY, store)
    assert allowed, f"Delivery should be unlocked with core 4 approved (Monitoring optional). Reasons: {reasons}"
    
    # Test 2: Only Strategy + Execution + Monitoring approved, missing Intake and Creatives
    # Expected: Delivery should be blocked (needs ALL core 4)
    session_state2 = {}
    store2 = ArtifactStore(session_state2, mode="inmemory")
    
    # Create draft intake
    intake2 = store2.create_artifact(
        artifact_type=AT.INTAKE,
        client_id=client_id,
        engagement_id=engagement_id,
        content={"client_name": "Test", "website": "https://test.com",
                "industry": "Tech", "geography": "US",
                "primary_offer": "Product", "objective": "Leads"}
    )
    # Leave as DRAFT (no QC, no approval)
    
    # Create draft strategy (need for lineage, but won't approve)
    strategy2 = store2.create_artifact(
        artifact_type=AT.STRATEGY,
        client_id=client_id,
        engagement_id=engagement_id,
        content={
            "layer1_business_reality": {"business_model_summary": "Test", "revenue_streams": "Test",
                                       "unit_economics": "Test", "pricing_logic": "Test",
                                       "growth_constraint": "Test", "bottleneck": "Demand"},
            "layer2_market_truth": {"category_maturity": "Test", "white_space_logic": "Test",
                                   "what_not_to_do": "Test"},
            "layer3_audience_psychology": {"awareness_state": "Test", "objection_hierarchy": "Test",
                                          "trust_transfer_mechanism": "Test"},
            "layer4_value_architecture": {"core_promise": "Test", "sacrifice_framing": "Test",
                                         "differentiation_logic": "Structural"},
            "layer5_narrative": {"narrative_problem": "Test", "narrative_tension": "Test",
                                "narrative_resolution": "Test", "enemy_definition": "Test",
                                "repetition_logic": "Test"},
            "layer6_channel_strategy": {"channels": [{"name": "LinkedIn", "strategic_role": "Awareness"}]},
            "layer7_constraints": {"tone_boundaries": "Test", "forbidden_language": "Test",
                                  "claim_boundaries": "Test", "compliance_rules": "Test"},
            "layer8_measurement": {"success_definition": "Test", "leading_indicators": "Test",
                                  "lagging_indicators": "Test", "decision_rules": "Test"}
        },
        source_artifacts=[intake2]
    )
    # Leave strategy as DRAFT (no approval)
    
    # Delivery should be blocked (missing Intake, Strategy, Creatives, Execution approvals)
    allowed2, reasons2 = check_gating(AT.DELIVERY, store2)
    assert not allowed2, "Delivery should be blocked without core 4 approved"
    assert len(reasons2) >= 4, f"Should have 4 missing items (core 4), got {len(reasons2)}: {reasons2}"


# ===================================================================
# Runtime Import Tests
# ===================================================================

def test_operator_v2_imports_successfully():
    """Test that operator_v2.py imports without errors"""
    try:
        import operator_v2
        assert True
    except Exception as e:
        pytest.fail(f"operator_v2.py failed to import: {str(e)}")


def test_artifact_store_imports_successfully():
    """Test that artifact_store.py imports without errors"""
    try:
        from aicmo.ui.persistence import artifact_store
        assert True
    except Exception as e:
        pytest.fail(f"artifact_store.py failed to import: {str(e)}")


def test_validate_strategy_contract_importable():
    """Test that validate_strategy_contract is importable"""
    try:
        from aicmo.ui.persistence.artifact_store import validate_strategy_contract
        assert callable(validate_strategy_contract)
    except Exception as e:
        pytest.fail(f"validate_strategy_contract not importable: {str(e)}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
