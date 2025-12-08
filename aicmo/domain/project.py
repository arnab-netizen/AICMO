"""Project domain models."""

from enum import Enum
from typing import Optional

from .base import AicmoBaseModel


class ProjectState(str, Enum):
    """Project state machine states."""

    NEW_LEAD = "NEW_LEAD"
    INTAKE_PENDING = "INTAKE_PENDING"
    INTAKE_CLARIFYING = "INTAKE_CLARIFYING"
    INTAKE_READY = "INTAKE_READY"

    STRATEGY_IN_PROGRESS = "STRATEGY_IN_PROGRESS"
    STRATEGY_DRAFT = "STRATEGY_DRAFT"
    STRATEGY_APPROVED = "STRATEGY_APPROVED"

    CREATIVE_IN_PROGRESS = "CREATIVE_IN_PROGRESS"
    CREATIVE_DRAFT = "CREATIVE_DRAFT"
    CREATIVE_APPROVED = "CREATIVE_APPROVED"

    EXECUTION_QUEUED = "EXECUTION_QUEUED"
    EXECUTION_IN_PROGRESS = "EXECUTION_IN_PROGRESS"
    EXECUTION_DONE = "EXECUTION_DONE"

    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class Project(AicmoBaseModel):
    """
    Domain model for a client project.
    
    Tracks the lifecycle of a marketing project from intake
    through strategy, creative development, and execution.
    """

    id: Optional[int] = None
    name: str
    state: ProjectState = ProjectState.STRATEGY_DRAFT
    
    # Client information
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    
    # Linked domain objects (IDs for now, can be expanded)
    intake_id: Optional[int] = None
    strategy_id: Optional[int] = None
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    notes: Optional[str] = None
    
    def can_transition_to(self, target_state: ProjectState) -> bool:
        """
        Check if transition from current state to target state is valid.
        
        Args:
            target_state: Desired target state
            
        Returns:
            True if transition is allowed
        """
        # Import here to avoid circular dependency
        from aicmo.core.workflow import is_valid_transition
        return is_valid_transition(self.state, target_state)
    
    def transition_to(self, target_state: ProjectState) -> "Project":
        """
        Transition project to a new state if valid.
        
        Args:
            target_state: Desired target state
            
        Returns:
            Updated project with new state
            
        Raises:
            ValueError: If transition is not valid
        """
        if not self.can_transition_to(target_state):
            raise ValueError(
                f"Invalid transition from {self.state.value} to {target_state.value}"
            )
        self.state = target_state
        return self
