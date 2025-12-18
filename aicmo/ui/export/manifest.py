"""
Manifest Builder for AICMO Delivery Packages

Creates deterministic, versioned manifests with checksums.
"""

import hashlib
import json
from typing import Dict, Any, List
from datetime import datetime


def build_delivery_manifest(
    config: 'DeliveryPackConfig',
    artifacts: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build delivery manifest from config and artifacts.
    
    Args:
        config: DeliveryPackConfig with selection and branding
        artifacts: Dict of artifact_type -> Artifact object
    
    Returns:
        Manifest dict with schema_version, ids, included_artifacts, checks, etc.
    """
    from aicmo.ui.export.export_models import DeliveryPackConfig
    
    manifest = {
        "schema_version": "delivery_manifest_v1",
        "generated_at": datetime.utcnow().isoformat(),
        
        # Context IDs
        "ids": {
            "campaign_id": config.campaign_id,
            "client_id": config.client_id,
            "engagement_id": config.engagement_id
        },
        
        # Included artifacts
        "included_artifacts": [],
        
        # Strategy schema version (if strategy included)
        "strategy_schema_version": None,
        
        # Export configuration
        "export_formats": config.formats,
        "branding": config.branding,
        
        # Pre-flight checks
        "checks": {
            "approvals_ok": False,
            "qc_ok": "unknown",
            "completeness_ok": False,
            "branding_ok": False,
            "legal_ok": False
        },
        
        # File index (filled after generation)
        "file_index": {},
        
        # Deterministic hash (computed after normalization)
        "manifest_hash": None
    }
    
    # Build included_artifacts list
    artifact_types = []
    if config.include_intake:
        artifact_types.append("intake")
    if config.include_strategy:
        artifact_types.append("strategy")
    if config.include_creatives:
        artifact_types.append("creatives")
    if config.include_execution:
        artifact_types.append("execution")
    if config.include_monitoring:
        artifact_types.append("monitoring")
    
    for artifact_type in artifact_types:
        artifact = artifacts.get(artifact_type)
        if artifact:
            manifest["included_artifacts"].append({
                "type": artifact_type,
                "status": artifact.status.value if hasattr(artifact.status, 'value') else str(artifact.status),
                "version": artifact.version,
                "updated_at": artifact.updated_at,
                "artifact_id": artifact.artifact_id
            })
            
            # Extract strategy schema version
            if artifact_type == "strategy":
                manifest["strategy_schema_version"] = artifact.content.get("schema_version", "NOT_SET")
    
    # Perform checks
    manifest["checks"]["approvals_ok"] = _check_approvals(artifacts, artifact_types)
    manifest["checks"]["completeness_ok"] = _check_completeness(artifacts, artifact_types)
    manifest["checks"]["branding_ok"] = _check_branding(config.branding)
    manifest["checks"]["legal_ok"] = True  # Placeholder - always true for now
    
    # QC check requires store access - mark unknown for now
    # Will be updated by export_engine if store is available
    
    return manifest


def finalize_manifest(manifest: Dict[str, Any], files: Dict[str, str]) -> Dict[str, Any]:
    """
    Finalize manifest with file index and compute deterministic hash.
    
    Args:
        manifest: Manifest dict (modified in place)
        files: Dict of format -> filepath
    
    Returns:
        Updated manifest with file_index and manifest_hash
    """
    # Add file index
    manifest["file_index"] = files.copy()
    
    # Compute deterministic hash (exclude hash field itself and file paths)
    manifest_for_hash = manifest.copy()
    manifest_for_hash.pop("manifest_hash", None)
    manifest_for_hash.pop("file_index", None)
    manifest_for_hash.pop("generated_at", None)  # Exclude timestamp for reproducibility
    
    # Normalize and hash
    normalized = json.dumps(manifest_for_hash, sort_keys=True)
    manifest["manifest_hash"] = hashlib.sha256(normalized.encode()).hexdigest()
    
    return manifest


def _check_approvals(artifacts: Dict[str, Any], artifact_types: List[str]) -> bool:
    """Check if all included artifacts are approved"""
    for artifact_type in artifact_types:
        artifact = artifacts.get(artifact_type)
        if not artifact:
            return False
        status = artifact.status.value if hasattr(artifact.status, 'value') else str(artifact.status)
        if status.lower() != "approved":
            return False
    return True


def _check_completeness(artifacts: Dict[str, Any], artifact_types: List[str]) -> bool:
    """Check if all requested artifacts exist"""
    for artifact_type in artifact_types:
        if artifact_type not in artifacts or artifacts[artifact_type] is None:
            return False
    return True


def _check_branding(branding: Dict[str, Any]) -> bool:
    """Check if branding is configured"""
    required = ["agency_name", "footer_text"]
    for field in required:
        if not branding.get(field):
            return False
    return True
