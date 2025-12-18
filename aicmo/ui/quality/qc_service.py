"""
QC Service - Orchestrate QC Generation and Persistence

This module connects the QC rules engine to the ArtifactStore,
providing a single entry point for running and persisting QC checks.
"""
from typing import Dict, Any
from datetime import datetime
import uuid

from aicmo.ui.persistence.artifact_store import Artifact, ArtifactStore, ArtifactType
from aicmo.ui.quality.qc_models import (
    QCArtifact,
    QCType,
    QCStatus,
    QCCheck,
    QCSummary,
    CheckSeverity,
    CheckStatus
)
from aicmo.ui.quality.rules import run_qc_for_artifact


# Mapping: ArtifactType -> QCType
ARTIFACT_TO_QC_TYPE = {
    ArtifactType.INTAKE: QCType.INTAKE_QC,
    ArtifactType.STRATEGY: QCType.STRATEGY_QC,
    ArtifactType.CREATIVES: QCType.CREATIVES_QC,
    ArtifactType.EXECUTION: QCType.EXECUTION_QC,
    ArtifactType.MONITORING: QCType.MONITORING_QC,
    ArtifactType.DELIVERY: QCType.DELIVERY_QC,
}


def run_and_persist_qc_for(
    artifact: Artifact,
    store: ArtifactStore,
    client_id: str,
    engagement_id: str,
    operator_id: str = "operator"
) -> QCArtifact:
    """
    Run QC rules and persist results to ArtifactStore.
    
    This is the single entry point for QC generation. It:
    1. Determines QC type from artifact type
    2. Runs deterministic rules engine (ruleset_v1)
    3. Converts results to QCArtifact
    4. Persists via ArtifactStore.store_qc_artifact()
    5. Returns QCArtifact
    
    Args:
        artifact: The artifact to check
        store: ArtifactStore instance
        client_id: Client ID for lineage
        engagement_id: Engagement ID for lineage
        operator_id: ID of operator running QC (default: "operator")
    
    Returns:
        QCArtifact with check results and status
    
    Raises:
        ValueError: If artifact type not supported for QC
    """
    # Determine QC type
    if artifact.artifact_type not in ARTIFACT_TO_QC_TYPE:
        raise ValueError(
            f"QC not supported for artifact type: {artifact.artifact_type}. "
            f"Supported types: {list(ARTIFACT_TO_QC_TYPE.keys())}"
        )
    
    qc_type = ARTIFACT_TO_QC_TYPE[artifact.artifact_type]
    
    # Run QC rules engine
    qc_result = run_qc_for_artifact(store, artifact)
    
    # QC result already has:
    # - qc_artifact_id
    # - qc_type
    # - target_artifact_id
    # - target_artifact_type
    # - target_version
    # - qc_status (computed)
    # - qc_score (computed)
    # - checks (from rules)
    # - summary (computed)
    # - model_used ("deterministic_ruleset_v1")
    # - created_at
    
    # Persist to ArtifactStore
    store.store_qc_artifact(qc_result)
    
    return qc_result


def get_qc_status_summary(qc_artifact: QCArtifact) -> Dict[str, Any]:
    """
    Extract human-readable summary from QCArtifact for UI display.
    
    Returns dict with:
        - status: "PASS" | "WARN" | "FAIL"
        - score: int (0-100)
        - blockers: int
        - majors: int
        - minors: int
        - blocker_messages: List[str] (failed BLOCKER check messages)
        - major_messages: List[str] (failed MAJOR check messages)
    """
    blocker_checks = [
        check for check in qc_artifact.checks
        if check.severity == CheckSeverity.BLOCKER and check.status == CheckStatus.FAIL
    ]
    
    major_checks = [
        check for check in qc_artifact.checks
        if check.severity == CheckSeverity.MAJOR and check.status == CheckStatus.FAIL
    ]
    
    return {
        "status": qc_artifact.qc_status.value,
        "score": qc_artifact.qc_score,
        "blockers": qc_artifact.summary.blockers,
        "majors": qc_artifact.summary.majors,
        "minors": qc_artifact.summary.minors,
        "blocker_messages": [check.message for check in blocker_checks],
        "major_messages": [check.message for check in major_checks],
        "blocker_evidence": [check.evidence for check in blocker_checks if check.evidence],
        "major_evidence": [check.evidence for check in major_checks if check.evidence],
    }


def format_qc_summary_text(qc_artifact: QCArtifact) -> str:
    """
    Format QC summary as text for UI display.
    
    Example output:
        QC Status: PASS ✅
        Score: 92/100
        Issues: 0 blockers, 1 major, 2 minors
    """
    status_emoji = {
        "PASS": "✅",
        "WARN": "⚠️",
        "FAIL": "❌"
    }
    
    emoji = status_emoji.get(qc_artifact.qc_status.value, "❓")
    
    summary_text = f"""**QC Status**: {qc_artifact.qc_status.value} {emoji}
**Score**: {qc_artifact.qc_score}/100
**Issues**: {qc_artifact.summary.blockers} blockers, {qc_artifact.summary.majors} majors, {qc_artifact.summary.minors} minors
"""
    
    return summary_text


def should_block_approval(qc_artifact: QCArtifact) -> bool:
    """
    Determine if QC result should block approval.
    
    Returns True if qc_status is FAIL (has BLOCKER failures).
    """
    return qc_artifact.qc_status == QCStatus.FAIL
