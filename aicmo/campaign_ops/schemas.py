"""
Pydantic schemas for Campaign Operations API and UI.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Campaign Schemas
# ============================================================================

class CampaignCreate(BaseModel):
    """Request to create a new campaign."""
    name: str = Field(..., description="Campaign name (must be unique)")
    client_name: str
    venture_name: Optional[str] = None
    objective: str
    platforms: List[str] = Field(default=["linkedin"], description="Platforms: linkedin, instagram, twitter, etc.")
    start_date: datetime
    end_date: datetime
    cadence: Dict[str, int] = Field(default={}, description="Posts per week per platform")
    primary_cta: str
    lead_capture_method: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Request to update a campaign."""
    name: Optional[str] = None
    objective: Optional[str] = None
    platforms: Optional[List[str]] = None
    cadence: Optional[Dict[str, int]] = None
    primary_cta: Optional[str] = None
    status: Optional[str] = None


class CampaignRead(BaseModel):
    """Campaign response."""
    id: int
    name: str
    client_name: str
    venture_name: Optional[str]
    objective: str
    platforms: List[str]
    start_date: datetime
    end_date: datetime
    cadence: Dict[str, int]
    primary_cta: str
    lead_capture_method: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Plan Schemas
# ============================================================================

class CampaignPlanCreate(BaseModel):
    """Request to create/update campaign plan."""
    angles: Optional[List[str]] = None
    positioning: Optional[str] = None
    messaging: Optional[Dict[str, List[str]]] = None
    weekly_themes: Optional[List[str]] = None


class CampaignPlanRead(BaseModel):
    """Campaign plan response."""
    id: int
    campaign_id: int
    angles_json: Optional[List[str]]
    positioning_json: Optional[str]
    messaging_json: Optional[Dict[str, List[str]]]
    weekly_themes_json: Optional[List[str]]
    generated_by: str
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Calendar Schemas
# ============================================================================

class CalendarItemCreate(BaseModel):
    """Request to create a calendar item."""
    platform: str
    content_type: str = "post"
    scheduled_at: datetime
    title: Optional[str] = None
    copy_text: Optional[str] = None
    asset_ref: Optional[str] = None
    cta_text: Optional[str] = None


class CalendarItemUpdate(BaseModel):
    """Request to update a calendar item."""
    platform: Optional[str] = None
    content_type: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    title: Optional[str] = None
    copy_text: Optional[str] = None
    asset_ref: Optional[str] = None
    cta_text: Optional[str] = None
    status: Optional[str] = None


class CalendarItemRead(BaseModel):
    """Calendar item response."""
    id: int
    campaign_id: int
    platform: str
    content_type: str
    scheduled_at: datetime
    title: Optional[str]
    copy_text: Optional[str]
    asset_ref: Optional[str]
    cta_text: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Task Schemas
# ============================================================================

class OperatorTaskCreate(BaseModel):
    """Request to create an operator task."""
    task_type: str = "POST"
    platform: str
    due_at: datetime
    title: str
    instructions_text: str
    copy_text: Optional[str] = None
    asset_ref: Optional[str] = None


class OperatorTaskUpdate(BaseModel):
    """Request to update an operator task."""
    status: Optional[str] = None
    copy_text: Optional[str] = None
    completion_proof_type: Optional[str] = None
    completion_proof_value: Optional[str] = None
    blocked_reason: Optional[str] = None


class OperatorTaskRead(BaseModel):
    """Operator task response."""
    id: int
    campaign_id: int
    calendar_item_id: Optional[int]
    task_type: str
    platform: str
    due_at: datetime
    title: str
    instructions_text: str
    copy_text: Optional[str]
    asset_ref: Optional[str]
    status: str
    completion_proof_type: Optional[str]
    completion_proof_value: Optional[str]
    completed_at: Optional[datetime]
    blocked_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Metric Schemas
# ============================================================================

class MetricEntryCreate(BaseModel):
    """Request to log a metric."""
    platform: str
    date: datetime
    metric_name: str
    metric_value: float
    notes: Optional[str] = None


class MetricEntryRead(BaseModel):
    """Metric entry response."""
    id: int
    campaign_id: int
    platform: str
    date: datetime
    metric_name: str
    metric_value: float
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Summary Schemas
# ============================================================================

class WeeklySummary(BaseModel):
    """Weekly campaign summary."""
    week_start: datetime
    week_end: datetime
    tasks_planned: int
    tasks_completed: int
    tasks_overdue: int
    top_platform: Optional[str] = None
    metrics_summary: Dict[str, Dict[str, float]] = {}  # platform -> {metric -> value}
    notes: str
