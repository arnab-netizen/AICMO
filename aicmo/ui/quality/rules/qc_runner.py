"""
QC Runner

Executes quality control rules for artifacts and aggregates results.
"""
import uuid
from datetime import datetime
from typing import Optional
from aicmo.ui.persistence.artifact_store import Artifact, ArtifactStore
from aicmo.ui.quality.qc_models import (
    QCArtifact,
    QCType,
    QCStatus,
    QCCheck,
    QCSummary,
    CheckStatus,
    CheckSeverity,
    CheckType
)
from .qc_registry import get_rules
from aicmo.ui.quality.schema_normalizer import normalize_schema_for_qc


# Map ArtifactType to QCType
ARTIFACT_TO_QC_TYPE = {
    "intake": QCType.INTAKE_QC,
    "strategy": QCType.STRATEGY_QC,
    "creatives": QCType.CREATIVES_QC,
    "execution": QCType.EXECUTION_QC,
    "delivery": QCType.DELIVERY_QC,
}


def run_qc_for_artifact(store: ArtifactStore, artifact: Artifact) -> QCArtifact:
    """
    Run all registered QC rules for an artifact and aggregate results.
    
    Args:
        store: ArtifactStore instance (for loading related artifacts if needed)
        artifact: The artifact to quality check
        
    Returns:
        QCArtifact with all check results and computed status/score
    
    Note: Content is normalized before rules run to accept both singular/plural forms.
    """
    # Normalize content before running rules (defensive schema handling)
    normalized_content = normalize_schema_for_qc(artifact.artifact_type.value, artifact.content)
    
    # Get rules for this artifact type
    rules = get_rules(artifact.artifact_type)
    
    # Run all rules on NORMALIZED content
    all_checks = []
    for rule_fn in rules:
        try:
            checks = rule_fn(normalized_content)
            all_checks.extend(checks)
        except Exception as e:
            # If a rule crashes, create a BLOCKER failure
            all_checks.append(QCCheck(
                check_id=f"rule_error_{rule_fn.__name__}",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.BLOCKER,
                message=f"Rule execution failed: {str(e)}",
                evidence=f"Exception in rule {rule_fn.__name__}: {type(e).__name__}"
            ))
    
    # Create QC artifact
    qc_type = ARTIFACT_TO_QC_TYPE.get(artifact.artifact_type.value)
    if not qc_type:
        # Fallback for unsupported types
        qc_type = QCType.INTAKE_QC
    
    qc_artifact = QCArtifact(
        qc_artifact_id=f"qc_{uuid.uuid4().hex[:12]}",
        qc_type=qc_type,
        target_artifact_id=artifact.artifact_id,
        target_artifact_type=artifact.artifact_type.value,
        target_version=artifact.version,
        qc_status=QCStatus.PASS,  # Will be computed
        qc_score=100,  # Will be computed
        checks=all_checks,
        summary=QCSummary(),
        model_used="deterministic_v1",
        created_at=datetime.utcnow().isoformat()
    )
    
    # Compute status and score
    qc_artifact.compute_status_and_summary()
    qc_artifact.compute_score()
    
    return qc_artifact


def has_blocking_failures(qc_artifact: Optional[QCArtifact]) -> bool:
    """
    Check if a QC artifact has any blocking failures.
    
    Args:
        qc_artifact: The QC artifact to check (can be None)
        
    Returns:
        True if there are any BLOCKER checks with FAIL status
    """
    if not qc_artifact:
        return False
    
    for check in qc_artifact.checks:
        if check.severity == CheckSeverity.BLOCKER and check.status == CheckStatus.FAIL:
            return True
    
    return False


def get_blocking_checks(qc_artifact: Optional[QCArtifact]) -> list[QCCheck]:
    """
    Get all blocking checks that failed.
    
    Args:
        qc_artifact: The QC artifact to check
        
    Returns:
        List of failed BLOCKER checks
    """
    if not qc_artifact:
        return []
    
    return [
        check for check in qc_artifact.checks
        if check.severity == CheckSeverity.BLOCKER and check.status == CheckStatus.FAIL
    ]
