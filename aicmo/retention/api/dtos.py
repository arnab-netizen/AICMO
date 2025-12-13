"""Retention - DTOs."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from aicmo.shared.ids import ClientId

class RenewalRiskDTO(BaseModel):
    client_id: ClientId
    risk_score: float  # 0.0 - 1.0
    risk_level: str  # "low", "medium", "high"
    factors: List[str]
    assessed_at: datetime

class UpsellOpportunityDTO(BaseModel):
    client_id: ClientId
    opportunity_type: str
    estimated_value: float
    confidence: float
    detected_at: datetime

class LifecycleStateDTO(BaseModel):
    client_id: ClientId
    stage: str  # "onboarding", "active", "at_risk", "churned"
    contract_end_date: Optional[datetime] = None
    last_engagement_at: Optional[datetime] = None

__all__ = ["RenewalRiskDTO", "UpsellOpportunityDTO", "LifecycleStateDTO"]
