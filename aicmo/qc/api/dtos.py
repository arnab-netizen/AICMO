"""QC - DTOs."""
from pydantic import BaseModel
from typing import List
from datetime import datetime
from aicmo.shared.ids import DraftId, QcResultId

class QcInputDTO(BaseModel):
    draft_id: DraftId
    benchmark_ids: List[str] = []

class QcIssueDTO(BaseModel):
    severity: str  # "critical", "major", "minor"
    section: str
    reason: str

class QcResultDTO(BaseModel):
    result_id: QcResultId
    draft_id: DraftId
    passed: bool
    score: float
    issues: List[QcIssueDTO]
    evaluated_at: datetime

__all__ = ["QcInputDTO", "QcIssueDTO", "QcResultDTO"]
