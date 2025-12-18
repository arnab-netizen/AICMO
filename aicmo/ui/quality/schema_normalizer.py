"""
Schema Normalizer for QC Rules

Purpose: Accept both singular and plural forms of artifact schema fields.

Design Rationale:
- QC rules expect singular forms (channel_plan, schedule, calendar, utm)
- Production code currently uses singular forms consistently
- Defensive programming: Accept both forms to prevent future drift
- Normalization happens BEFORE QC, so rules see canonical schema only

Example:
    Input:  {"channel_plans": [...], "schedules": {...}}
    Output: {"channel_plan": [...], "schedule": {...}}

Integration: Called from qc_service.py run_and_persist_qc_for() before passing
             content to ruleset.
"""

from typing import Dict, Any
import copy


def normalize_execution_schema(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Execution artifact schema to canonical singular forms.
    
    Accepts both singular and plural forms of:
    - channel_plan / channel_plans
    - schedule / schedules
    - calendar / calendars
    - utm / utms
    - cadence / cadences
    - governance / governances
    - resources / resources (already plural, but normalized for consistency)
    
    Args:
        content: Raw artifact content (may have plural keys)
    
    Returns:
        Normalized content with canonical singular keys
    
    Note: Creates defensive copy to avoid mutating original
    """
    # Defensive copy to avoid mutating original content
    normalized = copy.deepcopy(content)
    
    # Plural → Singular mappings
    plural_to_singular = {
        "channel_plans": "channel_plan",
        "schedules": "schedule",
        "calendars": "calendar",
        "utms": "utm",
        "cadences": "cadence",
        "governances": "governance",
        # "resources" is already plural, but keep for API consistency
    }
    
    # Apply normalization: if plural exists, move to singular
    for plural_key, singular_key in plural_to_singular.items():
        if plural_key in normalized:
            # Plural form found - migrate to singular
            if singular_key not in normalized:
                normalized[singular_key] = normalized[plural_key]
            # Remove plural form to avoid confusion
            del normalized[plural_key]
    
    return normalized


def normalize_creatives_schema(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Creatives artifact schema to canonical forms.
    
    Currently no plural/singular issues for Creatives, but included for
    future-proofing and API consistency.
    
    Args:
        content: Raw artifact content
    
    Returns:
        Normalized content (currently a defensive copy only)
    """
    # Defensive copy even if no normalization needed
    normalized = copy.deepcopy(content)
    
    # Future plural → singular mappings can be added here
    # Example: "hooks" → "hook" if needed
    
    return normalized


def normalize_strategy_schema(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Strategy artifact schema to canonical forms.
    
    Strategy uses 8-layer schema with consistent singular forms.
    No normalization currently needed, but included for API consistency.
    
    Args:
        content: Raw artifact content
    
    Returns:
        Normalized content (currently a defensive copy only)
    """
    # Defensive copy
    normalized = copy.deepcopy(content)
    
    # Strategy schema is already well-structured
    # Future normalization can be added here if needed
    
    return normalized


def normalize_delivery_schema(content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Delivery artifact schema to canonical forms.
    
    Delivery has manifest-based schema with included_artifacts list.
    No plural/singular issues currently.
    
    Args:
        content: Raw artifact content
    
    Returns:
        Normalized content (currently a defensive copy only)
    """
    # Defensive copy
    normalized = copy.deepcopy(content)
    
    # Delivery schema is manifest-based, no normalization needed
    
    return normalized


def normalize_schema_for_qc(artifact_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point: Normalize artifact schema before QC rules run.
    
    Routes to type-specific normalizer based on artifact_type.
    
    Args:
        artifact_type: Artifact type string (strategy, creatives, execution, delivery, etc.)
        content: Raw artifact content from artifact.content
    
    Returns:
        Normalized content with canonical schema
    
    Usage:
        from aicmo.ui.quality.schema_normalizer import normalize_schema_for_qc
        
        normalized_content = normalize_schema_for_qc(artifact.artifact_type.value, artifact.content)
        qc_result = ruleset.run_qc_for_artifact(artifact.artifact_type.value, normalized_content)
    """
    artifact_type_lower = artifact_type.lower()
    
    if artifact_type_lower == "execution":
        return normalize_execution_schema(content)
    
    elif artifact_type_lower == "creatives":
        return normalize_creatives_schema(content)
    
    elif artifact_type_lower == "strategy":
        return normalize_strategy_schema(content)
    
    elif artifact_type_lower == "delivery":
        return normalize_delivery_schema(content)
    
    else:
        # Unknown type or no normalization needed (intake, monitoring, etc.)
        # Return defensive copy anyway
        return copy.deepcopy(content)


# ===================================================================
# TESTING HELPERS
# ===================================================================

def test_normalization():
    """Self-test: Verify normalization works correctly"""
    
    # Test 1: Execution with plural forms
    input_execution = {
        "channel_plans": [{"name": "Instagram", "budget": 1000}],
        "schedules": {"monday": "9am", "friday": "5pm"},
        "calendars": {"type": "weekly"},
        "utms": {"source": "social", "medium": "paid"}
    }
    
    result = normalize_execution_schema(input_execution)
    
    assert "channel_plan" in result, "channel_plans should be normalized to channel_plan"
    assert "schedule" in result, "schedules should be normalized to schedule"
    assert "calendar" in result, "calendars should be normalized to calendar"
    assert "utm" in result, "utms should be normalized to utm"
    
    assert "channel_plans" not in result, "Plural form should be removed"
    assert "schedules" not in result, "Plural form should be removed"
    
    # Test 2: Execution with singular forms (no change needed)
    input_execution_singular = {
        "channel_plan": [{"name": "LinkedIn"}],
        "schedule": {"daily": "8am"}
    }
    
    result_singular = normalize_execution_schema(input_execution_singular)
    
    assert "channel_plan" in result_singular, "Singular form should be preserved"
    assert result_singular["channel_plan"] == [{"name": "LinkedIn"}], "Data should match"
    
    # Test 3: Mixed singular and plural (plural takes precedence only if singular missing)
    input_mixed = {
        "channel_plan": [{"name": "Existing"}],
        "channel_plans": [{"name": "New"}],
        "schedule": {"existing": "data"}
    }
    
    result_mixed = normalize_execution_schema(input_mixed)
    
    # If both exist, keep singular (don't overwrite)
    assert result_mixed["channel_plan"] == [{"name": "Existing"}], "Singular should not be overwritten"
    assert "channel_plans" not in result_mixed, "Plural form should be removed"
    
    # Test 4: Defensive copy (original not mutated)
    original = {"channel_plans": [{"name": "Test"}]}
    normalized = normalize_execution_schema(original)
    
    assert "channel_plans" in original, "Original should not be mutated"
    assert "channel_plan" in normalized, "Normalized should have singular"
    
    print("✅ All normalization tests passed!")


if __name__ == "__main__":
    test_normalization()
