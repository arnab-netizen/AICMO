from __future__ import annotations

from typing import Any
from aicmo.domain.state_machine import ProjectState


def is_client_ready(tenant_id: str, project_id: str, store: Any) -> bool:
    """Return True only if required artifacts are present, QC passed, and project state is QC_APPROVED."""
    required_types = ["INTAKE", "STRATEGY", "CREATIVES"]

    # Ensure latest artifacts exist and quality_contract.passes_semantic_qc == True
    for t in required_types:
        latest = store.latest(tenant_id, project_id, t)
        if not latest:
            return False
        # Quality contract
        qc = latest.get("quality_contract")
        if not qc or not qc.get("passes_semantic_qc"):
            return False

    # Check QC artifact exists and is PASS — try to locate QC by trace or with naming
    # We will look for a QC artifact referencing the latest strategy or creatives versions
    # Fallback: check project state stored elsewhere
    proj_state = None
    # Try to fetch a representative artifact and its state_at_creation
    representative = store.latest(tenant_id, project_id, "STRATEGY") or store.latest(tenant_id, project_id, "CREATIVES")
    if representative:
        proj_state = representative.get("state_at_creation") or representative.get("state")

    try:
        # If state is serialized as enum value
        if isinstance(proj_state, str) and proj_state == ProjectState.QC_APPROVED.value:
            return True
        # If state is enum-like
        if proj_state == ProjectState.QC_APPROVED:
            return True
    except Exception:
        pass

    return False
