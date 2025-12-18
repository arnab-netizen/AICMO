"""
QC-on-Approve Handler

Provides automatic QC generation for approval workflows.
When approving an artifact without prior QC, this module:
1. Detects missing QC
2. Runs QC using existing rules engine
3. Persists QC artifact
4. Returns QC result for gating decision

Canonical Tab IDs:
- "intake" (not "Client Intake")
- "strategy" (not "Strategy Contract")
- etc.

Integration:
- Called from operator_v2.py approval handlers
- Uses same QC engine as enforcement tests
- Persists to same ArtifactStore namespace
"""

from typing import Optional
from aicmo.ui.persistence.artifact_store import ArtifactStore, Artifact
from aicmo.ui.quality.qc_models import QCArtifact


# Canonical tab identifiers (internal persistence keys)
TAB_INTAKE = "intake"
TAB_STRATEGY = "strategy"
TAB_CREATIVES = "creatives"
TAB_EXECUTION = "execution"
TAB_MONITORING = "monitoring"
TAB_DELIVERY = "delivery"

# Display label to canonical tab ID mapping
DISPLAY_LABEL_TO_TAB_ID = {
    "Client Intake": TAB_INTAKE,
    "Intake": TAB_INTAKE,
    "Strategy Contract": TAB_STRATEGY,
    "Strategy": TAB_STRATEGY,
    "Creatives": TAB_CREATIVES,
    "Execution": TAB_EXECUTION,
    "Monitoring": TAB_MONITORING,
    "Delivery": TAB_DELIVERY,
}


def canonicalize_tab_id(display_label: str) -> str:
    """
    Normalize display labels to canonical tab IDs.
    
    Args:
        display_label: Human-readable label (e.g., "Client Intake")
    
    Returns:
        Canonical tab ID (e.g., "intake")
    
    Example:
        canonicalize_tab_id("Client Intake") -> "intake"
        canonicalize_tab_id("intake") -> "intake"
    """
    # If already canonical, return as-is
    if display_label in {TAB_INTAKE, TAB_STRATEGY, TAB_CREATIVES, TAB_EXECUTION, TAB_MONITORING, TAB_DELIVERY}:
        return display_label
    
    # Try mapping
    canonical = DISPLAY_LABEL_TO_TAB_ID.get(display_label)
    if canonical:
        return canonical
    
    # Fallback: lowercase and strip
    return display_label.lower().strip()


def ensure_qc_for_artifact(
    store: ArtifactStore,
    artifact: Artifact,
    client_id: str,
    engagement_id: str,
    operator_id: str = "operator"
) -> QCArtifact:
    """
    Ensure QC artifact exists for given artifact.
    If missing, runs QC and persists the result.
    
    Args:
        store: ArtifactStore instance
        artifact: Target artifact to QC
        client_id: Client identifier
        engagement_id: Engagement identifier
        operator_id: Operator performing QC (default: "operator")
    
    Returns:
        QCArtifact (existing or newly created)
    
    Behavior:
        - Attempts to fetch existing QC for artifact
        - If found and version matches → return existing
        - If missing or version mismatch → run QC, persist, return new
    
    Side Effects:
        - May create and persist new QC artifact
        - Uses same QC engine as enforcement tests (qc_service.py)
    """
    from aicmo.ui.quality.qc_service import run_and_persist_qc_for
    
    # Try to get existing QC
    existing_qc = store.get_qc_for_artifact(artifact)
    
    # If exists and version matches, return it
    if existing_qc and existing_qc.target_version == artifact.version:
        return existing_qc
    
    # Need to run QC (either missing or stale)
    # Use the same QC service that tests use
    qc_artifact = run_and_persist_qc_for(
        artifact=artifact,
        store=store,
        client_id=client_id,
        engagement_id=engagement_id,
        operator_id=operator_id
    )
    
    return qc_artifact
