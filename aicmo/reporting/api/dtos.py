"""Reporting - DTOs."""
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from aicmo.shared.ids import ReportId, ProjectId

class MetricPointDTO(BaseModel):
    name: str
    value: float
    unit: str
    timestamp: datetime

class MetricsSnapshotDTO(BaseModel):
    project_id: ProjectId
    metrics: List[MetricPointDTO]
    captured_at: datetime

class InsightDTO(BaseModel):
    insight_text: str
    confidence: float

class RecommendationDTO(BaseModel):
    action: str
    rationale: str
    impact_estimate: str

class ReportDTO(BaseModel):
    report_id: ReportId
    project_id: ProjectId
    metrics: List[MetricPointDTO]
    insights: List[InsightDTO]
    recommendations: List[RecommendationDTO]
    generated_at: datetime

__all__ = ["MetricPointDTO", "MetricsSnapshotDTO", "InsightDTO", "RecommendationDTO", "ReportDTO"]
