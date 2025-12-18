"""
Unified Gating Rules for AICMO Operator

Single source of truth for artifact dependencies.
Used by both artifact_store.py (backend) and operator_v2.py (UI).
"""

from enum import Enum
from typing import Dict, List, Optional

from aicmo.domain.state_machine import ProjectState


class IllegalStateTransitionError(RuntimeError):
    pass


class ArtifactType(str, Enum):
    """Artifact types matching operator workflow"""
    INTAKE = "intake"
    STRATEGY = "strategy"
    CREATIVES = "creatives"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    DELIVERY = "delivery"
    CAMPAIGN = "campaign"
    LEADGEN_REQUIREMENTS = "leadgen_requirements"


# ===================================================================
# CANONICAL GATING MAP
# ===================================================================

GATING_MAP: Dict[ArtifactType, List[ArtifactType]] = {
    ArtifactType.STRATEGY: [ArtifactType.INTAKE],
    ArtifactType.CREATIVES: [ArtifactType.STRATEGY],
    ArtifactType.EXECUTION: [ArtifactType.STRATEGY, ArtifactType.CREATIVES],
    ArtifactType.MONITORING: [ArtifactType.EXECUTION],
    ArtifactType.DELIVERY: [
        ArtifactType.INTAKE,
        ArtifactType.STRATEGY,
        ArtifactType.CREATIVES,
        ArtifactType.EXECUTION
    ],
}


# In-memory single-use override store (consumed when used)
_OVERRIDE_TOKEN: Optional[Dict[str, str]] = None


def require_override(reason: str, actor: str) -> None:
    """Register a one-time override for gating enforcement (in-memory only)."""
    global _OVERRIDE_TOKEN
    _OVERRIDE_TOKEN = {"reason": reason, "actor": actor}


def _consume_override() -> Optional[Dict[str, str]]:
    global _OVERRIDE_TOKEN
    if _OVERRIDE_TOKEN:
        token = _OVERRIDE_TOKEN
        _OVERRIDE_TOKEN = None
        return token
    return None


def require_state(current_state: ProjectState, required_state: ProjectState, action_name: str) -> None:
    """Ensure `current_state` matches `required_state` or raise IllegalStateTransitionError.

    The error message includes the action_name, current_state, and required_state.
    An override allows one illegal transition to proceed and is consumed.
    """
    if current_state == required_state:
        return

    # Allow a direct override once
    override = _consume_override()
    if override:
        return

    raise IllegalStateTransitionError(
        f"Action '{action_name}' blocked: current_state={current_state}, required_state={required_state}"
    )

# ===================================================================
# NOTES
# ===================================================================
# Rules:
# - Strategy requires Intake approved
# - Creatives requires Strategy approved
# - Execution requires Strategy + Creatives approved
# - Monitoring requires Execution approved
# - Delivery requires Intake + Strategy + Creatives + Execution approved (NOT Monitoring)
#
# Key insight: Delivery unlocks after core 4, Monitoring is optional for Delivery
