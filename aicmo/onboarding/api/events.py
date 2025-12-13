"""
Onboarding - Domain Events.
"""

from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import ClientId, BriefId, ProjectId


class IntakeCaptured(DomainEvent):
    """Event: Client intake form captured."""
    
    client_id: ClientId
    brief_id: BriefId
    form_version: str


class BriefValidated(DomainEvent):
    """
    Event: Brief normalized and validated.
    
    Triggers strategy generation.
    """
    
    brief_id: BriefId
    client_id: ClientId
    scope_deliverables: list[str]


class WorkspaceCreated(DomainEvent):
    """Event: Project workspace created."""
    
    project_id: ProjectId
    brief_id: BriefId
    workspace_url: str


__all__ = [
    "IntakeCaptured",
    "BriefValidated",
    "WorkspaceCreated",
]
