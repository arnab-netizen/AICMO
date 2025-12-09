"""
Project workflow state machine.

Phase 2: Implements state transitions and project lifecycle orchestration.
"""

from typing import Dict, Set
from aicmo.core.config import settings  # noqa: F401
from aicmo.domain.project import ProjectState


# Valid state transitions (from_state -> set of valid to_states)
VALID_TRANSITIONS: Dict[ProjectState, Set[ProjectState]] = {
    ProjectState.NEW_LEAD: {
        ProjectState.INTAKE_PENDING,
        ProjectState.CANCELLED,
    },
    ProjectState.INTAKE_PENDING: {
        ProjectState.INTAKE_CLARIFYING,
        ProjectState.INTAKE_READY,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.INTAKE_CLARIFYING: {
        ProjectState.INTAKE_READY,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.INTAKE_READY: {
        ProjectState.STRATEGY_IN_PROGRESS,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.STRATEGY_IN_PROGRESS: {
        ProjectState.STRATEGY_DRAFT,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.STRATEGY_DRAFT: {
        ProjectState.STRATEGY_IN_PROGRESS,  # Revision needed
        ProjectState.STRATEGY_APPROVED,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.STRATEGY_APPROVED: {
        ProjectState.CREATIVE_IN_PROGRESS,
        ProjectState.STRATEGY_IN_PROGRESS,  # Client wants changes
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.CREATIVE_IN_PROGRESS: {
        ProjectState.CREATIVE_DRAFT,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.CREATIVE_DRAFT: {
        ProjectState.CREATIVE_IN_PROGRESS,  # Revision needed
        ProjectState.CREATIVE_APPROVED,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.CREATIVE_APPROVED: {
        ProjectState.EXECUTION_QUEUED,
        ProjectState.CREATIVE_IN_PROGRESS,  # Client wants changes
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.EXECUTION_QUEUED: {
        ProjectState.EXECUTION_IN_PROGRESS,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.EXECUTION_IN_PROGRESS: {
        ProjectState.EXECUTION_DONE,
        ProjectState.CANCELLED,
        ProjectState.ON_HOLD,
    },
    ProjectState.EXECUTION_DONE: {
        # Terminal state - could add "reopen" if needed
        ProjectState.ON_HOLD,
    },
    ProjectState.ON_HOLD: {
        # Can resume from wherever it was paused
        ProjectState.INTAKE_PENDING,
        ProjectState.STRATEGY_IN_PROGRESS,
        ProjectState.CREATIVE_IN_PROGRESS,
        ProjectState.EXECUTION_IN_PROGRESS,
        ProjectState.CANCELLED,
    },
    ProjectState.CANCELLED: {
        # Terminal state - no transitions out
    },
}


def is_valid_transition(from_state: ProjectState, to_state: ProjectState) -> bool:
    """
    Check if a state transition is valid.
    
    Args:
        from_state: Current project state
        to_state: Desired target state
        
    Returns:
        True if transition is allowed by state machine
    """
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_valid_transitions(from_state: ProjectState) -> Set[ProjectState]:
    """
    Get all valid next states for a given state.
    
    Args:
        from_state: Current project state
        
    Returns:
        Set of valid target states
    """
    return VALID_TRANSITIONS.get(from_state, set())


def transition(project, to_state: ProjectState):
    """
    Transition a project to a new state if valid.
    
    Stage 1: Operates on Project domain model, which can be persisted
    via apply_to_campaign().
    
    Stage 4: Logs state transitions as learning events.
    
    Args:
        project: Project domain model
        to_state: Target state
        
    Returns:
        Updated project with new state
        
    Raises:
        ValueError: If transition is not valid
    """
    from aicmo.domain.project import Project
    
    if not is_valid_transition(project.state, to_state):
        raise ValueError(
            f"Invalid transition from {project.state.value} to {to_state.value}"
        )
    
    from_state = project.state
    project.state = to_state
    
    # Stage 4: Log state transition
    from aicmo.memory.engine import log_event
    log_event(
        "PROJECT_STATE_CHANGED",
        project_id=f"campaign_{project.campaign_id}" if project.campaign_id else None,
        details={
            "from_state": from_state.value,
            "to_state": to_state.value,
            "campaign_id": project.campaign_id
        },
        tags=["workflow", "state_transition", from_state.value, to_state.value]
    )
    
    return project
