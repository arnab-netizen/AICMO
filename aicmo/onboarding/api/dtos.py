"""
Onboarding - Data Transfer Objects.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from aicmo.shared.ids import ClientId, BriefId, ProjectId


class IntakeFormDTO(BaseModel):
    """Raw intake form responses."""
    
    responses: Dict[str, Any]  # Question ID -> Answer
    submitted_at: datetime


class DiscoveryNotesDTO(BaseModel):
    """Discovery call notes and clarifications."""
    
    notes: str
    clarifications: Dict[str, str] = {}
    attachments: List[str] = []  # URLs or file refs
    call_date: datetime


class ScopeDTO(BaseModel):
    """Project scope definition."""
    
    deliverables: List[str]
    exclusions: List[str] = []
    timeline_weeks: Optional[int] = None


class NormalizedBriefDTO(BaseModel):
    """Validated, normalized project brief."""
    
    brief_id: BriefId
    client_id: ClientId
    scope: ScopeDTO
    objectives: List[str]
    target_audience: str
    brand_guidelines: Dict[str, Any] = {}
    normalized_at: datetime


class ProjectSetupDTO(BaseModel):
    """Project workspace setup details."""
    
    project_id: ProjectId
    brief_id: BriefId
    workspace_url: Optional[str] = None
    created_at: datetime


class OnboardingStatusDTO(BaseModel):
    """Current onboarding progress."""
    
    client_id: ClientId
    stage: str  # "INTAKE", "DISCOVERY", "BRIEF_REVIEW", "WORKSPACE_SETUP", "COMPLETE"
    intake_complete: bool
    brief_validated: bool
    workspace_created: bool


__all__ = [
    "IntakeFormDTO",
    "DiscoveryNotesDTO",
    "ScopeDTO",
    "NormalizedBriefDTO",
    "ProjectSetupDTO",
    "OnboardingStatusDTO",
]
