"""
Strategy - Data Transfer Objects.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from aicmo.shared.ids import BriefId, StrategyId, ClientId


class StrategyInputDTO(BaseModel):
    """Input data for strategy generation."""
    
    brief_id: BriefId
    additional_context: Dict[str, Any] = {}


class KpiDTO(BaseModel):
    """Key Performance Indicator."""
    
    name: str
    target_value: float
    unit: str
    timeframe_days: int


class ChannelPlanDTO(BaseModel):
    """Marketing channel plan."""
    
    channel: str  # e.g., "linkedin", "google_ads"
    budget_allocation_pct: float
    tactics: List[str]


class TimelineDTO(BaseModel):
    """Project timeline."""
    
    milestones: List[Dict[str, str]]  # {name, week}
    duration_weeks: int


class StrategyDocDTO(BaseModel):
    """Complete strategy document."""
    
    strategy_id: StrategyId
    brief_id: BriefId
    version: int
    kpis: List[KpiDTO]
    channels: List[ChannelPlanDTO]
    timeline: TimelineDTO
    executive_summary: str
    is_approved: bool
    created_at: datetime
    approved_at: Optional[datetime] = None


class StrategyVersionDTO(BaseModel):
    """Lightweight strategy version metadata."""
    
    strategy_id: StrategyId
    version: int
    is_approved: bool
    created_at: datetime


__all__ = ["StrategyInputDTO", "KpiDTO", "ChannelPlanDTO", "TimelineDTO", "StrategyDocDTO", "StrategyVersionDTO"]
