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
    
    Stage 1: Project wraps CampaignDB as its persistent backing.
    No separate projects table - CampaignDB.project_state holds state.
    """

    id: Optional[int] = None
    campaign_id: Optional[int] = None  # FK to CampaignDB - required for persistence (optional for in-memory tests)
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
    
    @classmethod
    def from_campaign(cls, campaign) -> "Project":
        """
        Create a Project domain model from a CampaignDB instance.
        
        Args:
            campaign: CampaignDB instance (SQLAlchemy model)
            
        Returns:
            Project domain model
        """
        # Map campaign.project_state to ProjectState if available
        # Default to STRATEGY_DRAFT if not set
        project_state_str = getattr(campaign, "project_state", None)
        if project_state_str and hasattr(ProjectState, project_state_str):
            state = ProjectState(project_state_str)
        else:
            # Infer from strategy_status for backward compatibility
            strategy_status = getattr(campaign, "strategy_status", "DRAFT")
            if strategy_status == "APPROVED":
                state = ProjectState.STRATEGY_APPROVED
            elif strategy_status == "REJECTED":
                state = ProjectState.STRATEGY_DRAFT  # Back to draft
            else:
                state = ProjectState.STRATEGY_DRAFT
        
        return cls(
            id=campaign.id,
            campaign_id=campaign.id,
            name=campaign.name,
            state=state,
            client_name=getattr(campaign, "target_niche", None),
            notes=campaign.description,
            created_at=campaign.created_at.isoformat() if campaign.created_at else None,
            updated_at=campaign.updated_at.isoformat() if campaign.updated_at else None,
        )
    
    def apply_to_campaign(self, campaign):
        """
        Apply Project domain state back to a CampaignDB instance.
        
        Args:
            campaign: CampaignDB instance to update
            
        Returns:
            Updated CampaignDB instance
        """
        # Store project state in campaign.project_state
        campaign.project_state = self.state.value
        
        # Sync strategy_status for backward compatibility
        if self.state == ProjectState.STRATEGY_APPROVED:
            campaign.strategy_status = "APPROVED"
        elif self.state in {ProjectState.STRATEGY_IN_PROGRESS, ProjectState.STRATEGY_DRAFT}:
            campaign.strategy_status = "DRAFT"
        
        # Update other fields if changed
        if self.name:
            campaign.name = self.name
        if self.notes:
            campaign.description = self.notes
        
        return campaign
