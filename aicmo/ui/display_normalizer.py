"""
Display Schema Normalizer

Purpose: Normalize artifact schemas for UI rendering.
Ensures UI can handle both singular and plural forms of schema keys.

Design:
- Wraps raw artifact content with normalization layer
- UI code calls normalize_for_display() before accessing schema keys
- Uses same normalization logic as QC (schema_normalizer.py)
- Defensive programming: prevents UI crashes if backend changes to plural keys

Example Usage:
    artifact = store.get_artifact(ArtifactType.EXECUTION)
    content = normalize_for_display(artifact.content, artifact.artifact_type)
    channel_plan = content.get("channel_plan")  # Works with both singular/plural

Integration Points:
- operator_v2.py: Wrap content access for execution/delivery rendering
- Any UI code that reads artifact.content directly
"""

from typing import Dict, Any
from aicmo.ui.persistence.artifact_store import ArtifactType


def normalize_for_display(content: Dict[str, Any], artifact_type: ArtifactType) -> Dict[str, Any]:
    """
    Normalize artifact content for display.
    
    Args:
        content: Raw artifact content (may have plural or singular keys)
        artifact_type: Type of artifact (determines normalization rules)
    
    Returns:
        Normalized content with canonical singular keys
    
    Note: Reuses QC normalizer logic for consistency
    """
    if artifact_type == ArtifactType.EXECUTION:
        from aicmo.ui.quality.schema_normalizer import normalize_execution_schema
        return normalize_execution_schema(content)
    
    elif artifact_type == ArtifactType.DELIVERY:
        from aicmo.ui.quality.schema_normalizer import normalize_delivery_schema
        return normalize_delivery_schema(content)
    
    else:
        # Other artifact types don't have plural key issues
        return content


def safe_get(content: Dict[str, Any], key: str, *plural_variants, default=None) -> Any:
    """
    Safe get with plural fallback.
    
    Tries singular form first, then plural variants.
    
    Example:
        channel_plan = safe_get(content, "channel_plan", "channel_plans", default=[])
    
    Args:
        content: Artifact content dictionary
        key: Canonical singular key
        *plural_variants: Plural forms to try as fallback
        default: Default value if key not found
    
    Returns:
        Value from content, trying singular then plural forms
    """
    # Try canonical singular first
    if key in content:
        return content[key]
    
    # Try plural variants
    for variant in plural_variants:
        if variant in content:
            return content[variant]
    
    # Return default
    return default
