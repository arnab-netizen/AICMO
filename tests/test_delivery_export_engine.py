"""
Unit Tests for AICMO Delivery Export Engine

Tests manifest creation, hash determinism, and export generation.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path

from aicmo.ui.export.export_models import DeliveryPackConfig
from aicmo.ui.export.manifest import build_delivery_manifest, finalize_manifest
from aicmo.ui.export.render_json import render_delivery_json
from aicmo.ui.export.render_pdf import render_delivery_pdf
from aicmo.ui.export.render_zip import render_delivery_zip
from aicmo.ui.export.export_engine import generate_delivery_pack


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def mock_artifacts():
    """Create mock artifacts for testing"""
    from aicmo.ui.persistence.artifact_store import Artifact, ArtifactType, ArtifactStatus
    
    intake = Artifact(
        artifact_id="intake-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.INTAKE,
        version=1,
        status=ArtifactStatus.APPROVED,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        approved_at="2025-01-01T00:00:00",
        approved_by="operator",
        content={
            "client_name": "Test Company",
            "website": "https://test.com",
            "industry": "Technology",
            "geography": "US",
            "primary_offer": "SaaS Platform",
            "objective": "Leads"
        }
    )
    
    strategy = Artifact(
        artifact_id="strategy-123",
        client_id="client-123",
        engagement_id="eng-123",
        artifact_type=ArtifactType.STRATEGY,
        version=1,
        status=ArtifactStatus.APPROVED,
        created_at="2025-01-01T00:00:00",
        updated_at="2025-01-01T00:00:00",
        approved_at="2025-01-01T00:00:00",
        approved_by="operator",
        content={
            "schema_version": "strategy_contract_v1",
            "layer1_business_reality": {
                "business_model_summary": "B2B SaaS",
                "revenue_streams": "Subscriptions",
                "unit_economics": "CAC $500, LTV $5000",
                "pricing_logic": "Tiered",
                "growth_constraint": "Sales capacity",
                "bottleneck": "Awareness"
            },
            "layer2_market_truth": {
                "category_maturity": "Growth",
                "white_space_logic": "Mid-market underserved",
                "what_not_to_do": "Don't compete on price"
            },
            "layer3_audience_psychology": {
                "awareness_state": "Problem-aware",
                "objection_hierarchy": "Price, implementation, training",
                "trust_transfer_mechanism": "Testimonials"
            },
            "layer4_value_architecture": {
                "core_promise": "Reduce costs 30%",
                "sacrifice_framing": "Not for enterprises",
                "differentiation_logic": "Structural"
            },
            "layer5_narrative": {
                "narrative_problem": "Manual processes",
                "narrative_tension": "Competitors automating",
                "narrative_resolution": "Automate",
                "enemy_definition": "Manual work",
                "repetition_logic": "Automation vs Manual"
            },
            "layer6_channel_strategy": {
                "channels": [{"name": "LinkedIn", "strategic_role": "Awareness"}]
            },
            "layer7_constraints": {
                "tone_boundaries": "Professional",
                "forbidden_language": "No hype",
                "claim_boundaries": "Verified results only",
                "compliance_rules": "GDPR compliant"
            },
            "layer8_measurement": {
                "success_definition": "100 leads/month",
                "leading_indicators": "Engagement rate",
                "lagging_indicators": "Lead volume",
                "decision_rules": "Pause if quality < 50%"
            }
        }
    )
    
    return {
        "intake": intake,
        "strategy": strategy
    }


@pytest.fixture
def mock_config():
    """Create mock delivery pack config"""
    return DeliveryPackConfig(
        engagement_id="eng-123",
        client_id="client-123",
        campaign_id="camp-123",
        include_intake=True,
        include_strategy=True,
        include_creatives=False,
        include_execution=False,
        include_monitoring=False,
        formats=["json"],
        branding={
            "agency_name": "AICMO",
            "footer_text": "Prepared for Test Company",
            "primary_color": "#1E3A8A"
        }
    )


# ===================================================================
# Test Cases
# ===================================================================

def test_manifest_contains_ids_and_schema_version(mock_config, mock_artifacts):
    """Test that manifest includes required IDs and schema_version"""
    manifest = build_delivery_manifest(mock_config, mock_artifacts)
    
    # Check IDs
    assert "ids" in manifest
    assert manifest["ids"]["campaign_id"] == "camp-123"
    assert manifest["ids"]["client_id"] == "client-123"
    assert manifest["ids"]["engagement_id"] == "eng-123"
    
    # Check schema version
    assert manifest["schema_version"] == "delivery_manifest_v1"
    
    # Check strategy schema version extracted
    assert manifest["strategy_schema_version"] == "strategy_contract_v1"
    
    # Check included artifacts
    assert len(manifest["included_artifacts"]) == 2  # intake + strategy
    assert manifest["included_artifacts"][0]["type"] == "intake"
    assert manifest["included_artifacts"][1]["type"] == "strategy"


def test_manifest_hash_is_deterministic(mock_config, mock_artifacts):
    """Test that manifest hash is deterministic (same inputs = same hash)"""
    # Generate manifest twice with same inputs
    manifest1 = build_delivery_manifest(mock_config, mock_artifacts)
    finalize_manifest(manifest1, {"test.json": "/path/to/test.json"})
    
    manifest2 = build_delivery_manifest(mock_config, mock_artifacts)
    finalize_manifest(manifest2, {"test.json": "/path/to/test.json"})
    
    # Hashes should be identical (excluding generated_at timestamp)
    # Both should have the same content hash
    assert manifest1["manifest_hash"] == manifest2["manifest_hash"]
    assert len(manifest1["manifest_hash"]) == 64  # SHA256 hex length


def test_generate_json_outputs_files(mock_config, mock_artifacts, tmp_path):
    """Test that JSON renderer creates manifest.json and artifacts.json"""
    manifest = build_delivery_manifest(mock_config, mock_artifacts)
    
    files = render_delivery_json(str(tmp_path), manifest, mock_artifacts)
    
    # Check files created
    assert "manifest.json" in files
    assert "artifacts.json" in files
    
    # Check files exist
    assert os.path.exists(files["manifest.json"])
    assert os.path.exists(files["artifacts.json"])
    
    # Check JSON is valid
    with open(files["manifest.json"], 'r') as f:
        loaded_manifest = json.load(f)
        assert loaded_manifest["schema_version"] == "delivery_manifest_v1"
    
    with open(files["artifacts.json"], 'r') as f:
        loaded_artifacts = json.load(f)
        assert "intake" in loaded_artifacts
        assert "strategy" in loaded_artifacts


def test_generate_pdf_creates_file(mock_config, mock_artifacts, tmp_path):
    """Test that PDF renderer creates a PDF file"""
    manifest = build_delivery_manifest(mock_config, mock_artifacts)
    
    pdf_path = str(tmp_path / "test.pdf")
    result_path = render_delivery_pdf(pdf_path, manifest, mock_artifacts, mock_config.branding)
    
    # Check file created
    assert os.path.exists(result_path)
    assert result_path == pdf_path
    
    # Check file is not empty
    assert os.path.getsize(pdf_path) > 0


def test_generate_pptx_creates_file_hard_proof(mock_config, mock_artifacts, tmp_path):
    """HARD PROOF: Test that PPTX renderer creates a real PowerPoint file"""
    from aicmo.ui.export.render_pptx import render_delivery_pptx
    
    manifest = build_delivery_manifest(mock_config, mock_artifacts)
    
    pptx_path = str(tmp_path / "test.pptx")
    result_path = render_delivery_pptx(pptx_path, manifest, mock_artifacts, mock_config.branding)
    
    # Check file created
    assert os.path.exists(result_path), f"PPTX file not created at {result_path}"
    assert result_path == pptx_path
    
    # Check file is not empty (real PPTX files are at least 20KB)
    file_size = os.path.getsize(pptx_path)
    assert file_size > 0, f"PPTX file is empty (size: {file_size})"
    assert file_size > 20000, f"PPTX file too small (size: {file_size}), likely not a valid PowerPoint file"
    
    # Verify it's a valid ZIP archive (PPTX is ZIP-based)
    import zipfile
    assert zipfile.is_zipfile(pptx_path), "PPTX file is not a valid ZIP archive"
    
    # Verify it contains PPTX-specific files
    with zipfile.ZipFile(pptx_path, 'r') as zipf:
        names = zipf.namelist()
        assert any('ppt/' in name for name in names), "Missing ppt/ directory (not a valid PPTX)"
        assert any('slides' in name for name in names), "Missing slides (not a valid PPTX)"


def test_generate_zip_contains_manifest(mock_config, mock_artifacts, tmp_path):
    """Test that ZIP renderer creates ZIP with manifest and README"""
    import zipfile
    
    manifest = build_delivery_manifest(mock_config, mock_artifacts)
    
    # Create some test files
    test_file = tmp_path / "test.json"
    with open(test_file, 'w') as f:
        json.dump({"test": "data"}, f)
    
    files_dict = {"test.json": str(test_file)}
    
    zip_path = str(tmp_path / "test.zip")
    result_path = render_delivery_zip(zip_path, files_dict, manifest)
    
    # Check ZIP created
    assert os.path.exists(result_path)
    assert result_path == zip_path
    
    # Check ZIP contents
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        names = zipf.namelist()
        assert "README.txt" in names
        assert "test.json" in names
        
        # Check README content
        readme_content = zipf.read("README.txt").decode('utf-8')
        assert "AICMO Delivery Package" in readme_content
        assert "eng-123" in readme_content


def test_export_engine_generates_all_formats(mock_config, mock_artifacts, tmp_path):
    """Test that export engine generates all requested formats"""
    from aicmo.ui.persistence.artifact_store import ArtifactStore, ArtifactType
    
    # Create in-memory store
    session_state = {}
    store = ArtifactStore(session_state, mode="inmemory")
    
    # Store artifacts
    for artifact in mock_artifacts.values():
        key = f"artifact_{artifact.artifact_type.value}"
        session_state[key] = artifact.to_dict()
    
    # Configure to generate PDF, JSON, and ZIP
    config = DeliveryPackConfig(
        engagement_id="eng-123",
        client_id="client-123",
        campaign_id="camp-123",
        include_intake=True,
        include_strategy=True,
        include_creatives=False,
        include_execution=False,
        include_monitoring=False,
        formats=["pdf", "json", "zip"],
        branding={"agency_name": "AICMO", "footer_text": "Test", "primary_color": "#1E3A8A"}
    )
    
    # Generate with custom output dir
    result = generate_delivery_pack(store, config, output_base_dir=str(tmp_path))
    
    # Check result
    assert result.manifest is not None
    assert result.files is not None
    assert result.generated_at is not None
    
    # Check files generated
    assert "pdf" in result.files
    assert "manifest.json" in result.files
    assert "zip" in result.files
    
    # Check files exist
    for filepath in result.files.values():
        assert os.path.exists(filepath), f"File not found: {filepath}"
    
    # Check manifest has hash
    assert result.manifest["manifest_hash"] is not None
    assert len(result.manifest["manifest_hash"]) == 64


def test_manifest_checks_all_fields(mock_config, mock_artifacts):
    """Test that manifest includes all required check fields"""
    manifest = build_delivery_manifest(mock_config, mock_artifacts)
    
    assert "checks" in manifest
    checks = manifest["checks"]
    
    # All check fields present
    assert "approvals_ok" in checks
    assert "qc_ok" in checks
    assert "completeness_ok" in checks
    assert "branding_ok" in checks
    assert "legal_ok" in checks
    
    # Approvals should be True (mock artifacts are approved)
    assert checks["approvals_ok"] is True
    
    # QC should be unknown (no store access in unit test)
    assert checks["qc_ok"] == "unknown"
    
    # Completeness should be True (requested artifacts exist)
    assert checks["completeness_ok"] is True
    
    # Branding should be True (config has required fields)
    assert checks["branding_ok"] is True


def test_config_to_dict_roundtrip(mock_config):
    """Test that DeliveryPackConfig serializes and deserializes correctly"""
    # Convert to dict
    config_dict = mock_config.to_dict()
    
    # Check keys present
    assert "engagement_id" in config_dict
    assert "formats" in config_dict
    assert "branding" in config_dict
    
    # Roundtrip
    config_restored = DeliveryPackConfig.from_dict(config_dict)
    
    # Check values match
    assert config_restored.engagement_id == mock_config.engagement_id
    assert config_restored.formats == mock_config.formats
    assert config_restored.branding == mock_config.branding
