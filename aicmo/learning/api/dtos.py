"""Learning - DTOs."""
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from aicmo.shared.ids import ProjectId

class LearningEventDTO(BaseModel):
    event_type: str
    context: Dict[str, Any]
    outcome: Optional[Dict[str, Any]] = None
    timestamp: datetime

class ContextQueryDTO(BaseModel):
    query_text: str
    filters: Dict[str, Any] = {}
    limit: int = 10

class ContextResultDTO(BaseModel):
    results: List[Dict[str, Any]]
    relevance_scores: List[float]

class StoredArtifactDTO(BaseModel):
    artifact_type: str
    project_id: Optional[ProjectId] = None
    content: str
    metadata: Dict[str, Any] = {}
    stored_at: datetime

__all__ = ["LearningEventDTO", "ContextQueryDTO", "ContextResultDTO", "StoredArtifactDTO"]
