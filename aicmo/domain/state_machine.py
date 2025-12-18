from enum import Enum
from typing import Tuple, Set


class ProjectState(Enum):
    CREATED = "CREATED"
    INTAKE_COMPLETE = "INTAKE_COMPLETE"
    STRATEGY_GENERATED = "STRATEGY_GENERATED"
    STRATEGY_APPROVED = "STRATEGY_APPROVED"
    CAMPAIGN_DEFINED = "CAMPAIGN_DEFINED"
    CREATIVE_GENERATED = "CREATIVE_GENERATED"
    QC_FAILED = "QC_FAILED"
    QC_APPROVED = "QC_APPROVED"
    DELIVERED = "DELIVERED"


# Define allowed transitions as a set of tuples
_ALLOWED_TRANSITIONS: Set[Tuple[ProjectState, ProjectState]] = {
    (ProjectState.CREATED, ProjectState.INTAKE_COMPLETE),
    (ProjectState.INTAKE_COMPLETE, ProjectState.STRATEGY_GENERATED),
    (ProjectState.STRATEGY_GENERATED, ProjectState.STRATEGY_APPROVED),
    (ProjectState.STRATEGY_APPROVED, ProjectState.CAMPAIGN_DEFINED),
    (ProjectState.CAMPAIGN_DEFINED, ProjectState.CREATIVE_GENERATED),
    (ProjectState.CREATIVE_GENERATED, ProjectState.QC_FAILED),
    (ProjectState.CREATIVE_GENERATED, ProjectState.QC_APPROVED),
    (ProjectState.QC_FAILED, ProjectState.QC_APPROVED),
    (ProjectState.QC_APPROVED, ProjectState.DELIVERED),
}


def can_transition(from_state: ProjectState, to_state: ProjectState) -> bool:
    """Return True if transition is explicitly allowed by spec."""
    return (from_state, to_state) in _ALLOWED_TRANSITIONS
