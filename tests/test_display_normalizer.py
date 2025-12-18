"""
Display Normalizer Tests

Proves UI display normalizer can handle both singular and plural schema keys.
"""
import pytest
from aicmo.ui.display_normalizer import normalize_for_display, safe_get
from aicmo.ui.persistence.artifact_store import ArtifactType


def test_normalize_execution_singular_keys():
    """Canonical singular keys pass through unchanged"""
    content = {
        "channel_plan": [{"channel": "linkedin"}],
        "schedule": "Week 1-4",
        "cadence": "Daily",
        "utm_plan": "utm_campaign=test"
    }
    
    normalized = normalize_for_display(content, ArtifactType.EXECUTION)
    
    assert normalized["channel_plan"] == [{"channel": "linkedin"}]
    assert normalized["schedule"] == "Week 1-4"
    assert normalized["cadence"] == "Daily"
    assert normalized["utm_plan"] == "utm_campaign=test"


def test_normalize_execution_plural_keys():
    """Plural keys get normalized to singular"""
    content = {
        "channel_plans": [{"channel": "facebook"}, {"channel": "twitter"}],
        "schedules": "Week 1-8",
        "utms": {"source": "social"}
    }
    
    normalized = normalize_for_display(content, ArtifactType.EXECUTION)
    
    # Plural keys should be normalized to singular
    assert "channel_plan" in normalized
    assert normalized["channel_plan"] == [{"channel": "facebook"}, {"channel": "twitter"}]
    
    assert "schedule" in normalized
    assert normalized["schedule"] == "Week 1-8"
    
    assert "utm" in normalized
    assert normalized["utm"] == {"source": "social"}
    
    # Plural forms should be removed
    assert "channel_plans" not in normalized
    assert "schedules" not in normalized
    assert "utms" not in normalized


def test_normalize_execution_mixed_keys():
    """Mix of singular and plural - singular takes precedence"""
    content = {
        "channel_plan": [{"channel": "instagram"}],  # Singular
        "schedules": "Week 1-2",  # Plural
        "cadence": "Weekly"  # Singular
    }
    
    normalized = normalize_for_display(content, ArtifactType.EXECUTION)
    
    assert normalized["channel_plan"] == [{"channel": "instagram"}]
    assert normalized["schedule"] == "Week 1-2"
    assert normalized["cadence"] == "Weekly"


def test_normalize_delivery_singular_keys():
    """Delivery passes through (no normalization currently implemented)"""
    content = {
        "manifest": {
            "schema_version": "delivery_manifest_v1",
            "included_artifacts": [{"type": "strategy"}],
            "generation_plan": {"selected_job_ids": ["strategy_job"]}
        }
    }
    
    normalized = normalize_for_display(content, ArtifactType.DELIVERY)
    
    # Delivery normalizer currently returns defensive copy only
    manifest = normalized["manifest"]
    assert "included_artifacts" in manifest
    assert "generation_plan" in manifest


def test_normalize_delivery_plural_keys():
    """Delivery currently doesn't normalize - documents current behavior"""
    content = {
        "manifest": {
            "schema_version": "delivery_manifest_v1",
            "included_artifacts": [{"type": "strategy"}, {"type": "creatives"}]
        }
    }
    
    normalized = normalize_for_display(content, ArtifactType.DELIVERY)
    
    # Note: Delivery normalizer doesn't currently do transformations
    # This test documents current behavior (future enhancement opportunity)
    manifest = normalized["manifest"]
    assert "included_artifacts" in manifest


def test_safe_get_singular_present():
    """safe_get returns value from singular key when present"""
    content = {"channel_plan": [{"channel": "linkedin"}]}
    
    result = safe_get(content, "channel_plan", "channel_plans", default=[])
    
    assert result == [{"channel": "linkedin"}]


def test_safe_get_plural_fallback():
    """safe_get falls back to plural when singular missing"""
    content = {"channel_plans": [{"channel": "facebook"}]}
    
    result = safe_get(content, "channel_plan", "channel_plans", default=[])
    
    assert result == [{"channel": "facebook"}]


def test_safe_get_default():
    """safe_get returns default when neither singular nor plural present"""
    content = {"other_field": "value"}
    
    result = safe_get(content, "channel_plan", "channel_plans", default=[])
    
    assert result == []


def test_safe_get_singular_precedence():
    """safe_get prefers singular even if plural also present"""
    content = {
        "channel_plan": [{"channel": "linkedin"}],
        "channel_plans": [{"channel": "facebook"}]
    }
    
    result = safe_get(content, "channel_plan", "channel_plans")
    
    # Should return singular value
    assert result == [{"channel": "linkedin"}]


def test_normalize_for_display_other_artifact_types():
    """Non-execution/delivery artifacts pass through unchanged"""
    content = {
        "client_name": "Test Corp",
        "website": "https://test.com"
    }
    
    # Test with INTAKE (no normalization needed)
    normalized = normalize_for_display(content, ArtifactType.INTAKE)
    
    assert normalized == content
    assert normalized is content  # Should be same object (no copy needed)
