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
