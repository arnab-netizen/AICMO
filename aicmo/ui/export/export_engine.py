"""
Export Engine for AICMO Delivery Packages

Orchestrates generation of all export formats.
"""

import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from aicmo.ui.export.export_models import DeliveryPackConfig, DeliveryPackResult
from aicmo.ui.export.manifest import build_delivery_manifest, finalize_manifest
from aicmo.ui.export.render_pdf import render_delivery_pdf
from aicmo.ui.export.render_pptx import render_delivery_pptx
from aicmo.ui.export.render_json import render_delivery_json
from aicmo.ui.export.render_zip import render_delivery_zip


def generate_delivery_pack(
    store,
    config: DeliveryPackConfig,
    output_base_dir: str = None
) -> DeliveryPackResult:
    """
    Generate complete delivery package with all selected formats.
    
    Args:
        store: ArtifactStore instance
        config: DeliveryPackConfig with selection and branding
        output_base_dir: Base directory for exports (default: /workspaces/AICMO/exports)
    
    Returns:
        DeliveryPackResult with manifest, files, and metadata
    """
    from aicmo.ui.persistence.artifact_store import ArtifactType
    
    # Default output directory
    if output_base_dir is None:
        output_base_dir = "/workspaces/AICMO/exports"
    
    # Create output directory with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(
        output_base_dir,
        config.engagement_id,
        timestamp
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # Load artifacts
    artifacts = {}
    artifact_types = []
    
    if config.include_intake:
        artifact_types.append(ArtifactType.INTAKE)
    if config.include_strategy:
        artifact_types.append(ArtifactType.STRATEGY)
    if config.include_creatives:
        artifact_types.append(ArtifactType.CREATIVES)
    if config.include_execution:
        artifact_types.append(ArtifactType.EXECUTION)
    if config.include_monitoring:
        artifact_types.append(ArtifactType.MONITORING)
    
    for artifact_type in artifact_types:
        artifact = store.get_artifact(artifact_type)
        if artifact:
            artifacts[artifact_type.value] = artifact
    
    # Build manifest
    manifest = build_delivery_manifest(config, artifacts)
    
    # Check QC status if store has QC artifacts
    qc_status = _check_qc_status(store, artifacts)
    manifest["checks"]["qc_ok"] = qc_status
    
    # Generate exports
    generated_files = {}
    
    # PDF
    if "pdf" in config.formats:
        pdf_path = os.path.join(output_dir, f"delivery_{config.engagement_id}.pdf")
        render_delivery_pdf(pdf_path, manifest, artifacts, config.branding)
        generated_files["pdf"] = pdf_path
    
    # PPTX
    if "pptx" in config.formats:
        pptx_path = os.path.join(output_dir, f"delivery_{config.engagement_id}.pptx")
        render_delivery_pptx(pptx_path, manifest, artifacts, config.branding)
        generated_files["pptx"] = pptx_path
    
    # JSON
    if "json" in config.formats:
        json_files = render_delivery_json(output_dir, manifest, artifacts)
        generated_files.update(json_files)
    
    # ZIP (includes all previously generated files)
    if "zip" in config.formats:
        zip_path = os.path.join(output_dir, f"delivery_{config.engagement_id}.zip")
        render_delivery_zip(zip_path, generated_files, manifest)
        generated_files["zip"] = zip_path
    
    # Finalize manifest with file index and hash
    manifest = finalize_manifest(manifest, generated_files)
    
    # Save final manifest
    import json
    manifest_final_path = os.path.join(output_dir, "manifest_final.json")
    with open(manifest_final_path, 'w') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    generated_files["manifest_final.json"] = manifest_final_path
    
    # Create result
    result = DeliveryPackResult(
        manifest=manifest,
        files=generated_files,
        generated_at=datetime.utcnow().isoformat(),
        output_dir=output_dir
    )
    
    return result


def _check_qc_status(store, artifacts: Dict[str, Any]) -> str:
    """
    Check QC status for included artifacts.
    
    Returns: "pass", "fail", or "unknown"
    """
    try:
        from aicmo.ui.quality.qc_models import QCStatus
        
        has_any_qc = False
        all_pass = True
        
        for artifact in artifacts.values():
            if artifact:
                qc_artifact = store.get_qc_for_artifact(artifact)
                if qc_artifact:
                    has_any_qc = True
                    if qc_artifact.qc_status != QCStatus.PASS:
                        all_pass = False
                        break
        
        if not has_any_qc:
            return "unknown"
        
        return "pass" if all_pass else "fail"
    
    except Exception:
        return "unknown"
