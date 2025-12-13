"""Client Review - DTOs."""
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from aicmo.shared.ids import DraftId, ReviewPackageId, ClientId

class ReviewPackageDTO(BaseModel):
    package_id: ReviewPackageId
    draft_id: DraftId
    review_url: str
    sent_at: datetime

class ClientFeedbackDTO(BaseModel):
    feedback_text: str
    requested_changes: List[str] = []
    approval_status: str  # "approved", "changes_requested", "rejected"
    submitted_at: datetime

class RevisionRequestDTO(BaseModel):
    section: str
    change_description: str
    priority: str

class RevisionPlanDTO(BaseModel):
    package_id: ReviewPackageId
    revision_requests: List[RevisionRequestDTO]
    estimated_hours: float

__all__ = ["ReviewPackageDTO", "ClientFeedbackDTO", "RevisionRequestDTO", "RevisionPlanDTO"]
