"""
JSON Renderer for AICMO Delivery Packages

Exports manifest and artifacts as clean JSON files.
"""

import json
import os
from typing import Dict, Any


def render_delivery_json(
    output_dir: str,
    manifest: Dict[str, Any],
    artifacts: Dict[str, Any]
) -> Dict[str, str]:
    """
    Generate JSON export files.
    
    Args:
        output_dir: Output directory path
        manifest: Delivery manifest dict
        artifacts: Dict of artifact_type -> Artifact
    
    Returns:
        Dict of filename -> filepath
    """
    files = {}
    
    # Save manifest
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    files["manifest.json"] = manifest_path
    
    # Save artifacts
    artifacts_export = {}
    for artifact_type, artifact in artifacts.items():
        if artifact:
            artifacts_export[artifact_type] = {
                "artifact_id": artifact.artifact_id,
                "version": artifact.version,
                "status": artifact.status.value if hasattr(artifact.status, 'value') else str(artifact.status),
                "created_at": artifact.created_at,
                "updated_at": artifact.updated_at,
                "approved_at": artifact.approved_at,
                "approved_by": artifact.approved_by,
                "content": artifact.content,
                "notes": artifact.notes
            }
    
    artifacts_path = os.path.join(output_dir, "artifacts.json")
    with open(artifacts_path, 'w') as f:
        json.dump(artifacts_export, f, indent=2, sort_keys=True)
    files["artifacts.json"] = artifacts_path
    
    return files
