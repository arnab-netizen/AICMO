"""
QC Persistence

Manages storage and retrieval of QC artifacts in the session state.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from aicmo.ui.persistence.artifact_store import ArtifactStore, ArtifactType
from aicmo.ui.quality.qc_models import QCArtifact, QCType


def save_qc_result(
    store: ArtifactStore,
    qc_artifact: QCArtifact,
    client_id: str,
    engagement_id: str,
    source_artifact_id: str
) -> None:
    """
    Save a QC artifact result to session state.
    
    QC artifacts are stored with keys like:
    qc_{artifact_type}_{engagement_id}
    
    Args:
        store: ArtifactStore instance (provides session_state)
        qc_artifact: The QC artifact to save
        client_id: Client ID for lineage
        engagement_id: Engagement ID for lineage
        source_artifact_id: The artifact that was checked
    """
    # Add lineage metadata
    qc_data = qc_artifact.to_dict()
    qc_data["client_id"] = client_id
    qc_data["engagement_id"] = engagement_id
    qc_data["source_artifact_id"] = source_artifact_id
    qc_data["saved_at"] = datetime.utcnow().isoformat()
    
    # Store in session state
    # Key format: qc_{target_type}_{engagement_id}
    key = f"qc_{qc_artifact.target_artifact_type}_{engagement_id}"
    store.session_state[key] = qc_data


def load_latest_qc(
    store: ArtifactStore,
    artifact_type: str,
    engagement_id: str
) -> Optional[QCArtifact]:
    """
    Load the latest QC result for an artifact type in an engagement.
    
    Args:
        store: ArtifactStore instance
        artifact_type: The artifact type (as string, e.g. "strategy")
        engagement_id: The engagement ID
        
    Returns:
        QCArtifact if found, None otherwise
    """
    key = f"qc_{artifact_type}_{engagement_id}"
    qc_data = store.session_state.get(key)
    
    if not qc_data:
        return None
    
    try:
        return QCArtifact.from_dict(qc_data)
    except Exception:
        # If deserialization fails, return None
        return None


def get_qc_for_artifact(
    store: ArtifactStore,
    artifact_type: ArtifactType,
    engagement_id: str
) -> Optional[QCArtifact]:
    """
    Get QC artifact for a specific artifact type and engagement.
    
    Args:
        store: ArtifactStore instance
        artifact_type: The artifact type enum
        engagement_id: The engagement ID
        
    Returns:
        QCArtifact if found, None otherwise
    """
    return load_latest_qc(store, artifact_type.value, engagement_id)


def get_all_qc_for_engagement(
    store: ArtifactStore,
    engagement_id: str
) -> Dict[str, Optional[QCArtifact]]:
    """
    Get all QC artifacts for an engagement.
    
    Args:
        store: ArtifactStore instance
        engagement_id: The engagement ID
        
    Returns:
        Dict mapping artifact type to QCArtifact (or None if no QC run)
    """
    results = {}
    
    for artifact_type in ["intake", "strategy", "creatives", "execution", "monitoring", "delivery"]:
        qc = load_latest_qc(store, artifact_type, engagement_id)
        results[artifact_type] = qc
    
    return results
