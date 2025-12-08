"""
CAM (Client Acquisition Mode) API Schemas.

Pydantic models for CAM Phase 7-9 API endpoints.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from aicmo.cam.discovery_domain import Platform


# ==========================================
# PHASE 7: DISCOVERY
# ==========================================

class CamDiscoveryCriteria(BaseModel):
    """Search criteria for lead discovery."""
    platforms: List[Platform]
    keywords: List[str]
    location: Optional[str] = None
    role_contains: Optional[str] = None
    min_followers: Optional[int] = None
    recent_activity_days: Optional[int] = 30


class CamDiscoveryJobCreate(BaseModel):
    """Request to create a discovery job."""
    name: str
    campaign_id: Optional[int] = None
    criteria: CamDiscoveryCriteria


class CamDiscoveryJobOut(BaseModel):
    """Discovery job response."""
    id: int
    name: str
    campaign_id: Optional[int]
    criteria: dict  # Serialized DiscoveryCriteria
    status: str  # PENDING/RUNNING/DONE/FAILED
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class CamDiscoveredProfileOut(BaseModel):
    """Discovered profile response."""
    id: int
    job_id: int
    platform: str
    handle: str
    profile_url: str
    display_name: str
    bio: Optional[str] = None
    followers: Optional[int] = None
    location: Optional[str] = None
    match_score: float
    discovered_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CamConvertProfilesRequest(BaseModel):
    """Request to convert profiles to leads."""
    profile_ids: List[int]


class CamConvertProfilesResponse(BaseModel):
    """Response after converting profiles."""
    leads_created: int
    message: str


# ==========================================
# PHASE 8: PIPELINE & APPOINTMENTS (Placeholders)
# ==========================================

class CamPipelineSummary(BaseModel):
    """Pipeline summary statistics."""
    campaign_id: int
    new_count: int = 0
    contacted_count: int = 0
    replied_count: int = 0
    qualified_count: int = 0
    won_count: int = 0
    lost_count: int = 0


class CamLeadStageUpdateRequest(BaseModel):
    """Request to update lead stage."""
    stage: str  # NEW/CONTACTED/REPLIED/QUALIFIED/WON/LOST


class CamContactEventIn(BaseModel):
    """Request to log a contact event."""
    channel: str  # email/linkedin/etc
    direction: str  # OUTBOUND/INBOUND
    summary: str


class CamContactEventOut(BaseModel):
    """Contact event response."""
    id: int
    lead_id: int
    channel: str
    direction: str
    summary: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CamAppointmentIn(BaseModel):
    """Request to create an appointment."""
    lead_id: int
    scheduled_for: datetime
    duration_minutes: int = 30
    location: Optional[str] = None  # Zoom/Meet/Phone
    calendar_link: Optional[str] = None
    notes: Optional[str] = None


class CamAppointmentOut(BaseModel):
    """Appointment response."""
    id: int
    lead_id: int
    scheduled_for: datetime
    duration_minutes: int
    location: Optional[str]
    calendar_link: Optional[str]
    notes: Optional[str]
    status: str  # SCHEDULED/COMPLETED/CANCELLED
    
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PHASE 9: SAFETY (Placeholders)
# ==========================================

class CamChannelLimitConfig(BaseModel):
    """Per-channel rate limit configuration."""
    channel: str
    max_per_day: int
    warmup_enabled: bool = False
    warmup_start: Optional[int] = None
    warmup_increment: Optional[int] = None
    warmup_max: Optional[int] = None


class CamSafetySettings(BaseModel):
    """Safety and compliance settings."""
    per_channel_limits: dict[str, CamChannelLimitConfig] = Field(default_factory=dict)
    send_window_start: Optional[str] = None  # HH:MM format
    send_window_end: Optional[str] = None  # HH:MM format
    blocked_domains: List[str] = Field(default_factory=list)
    do_not_contact_emails: List[str] = Field(default_factory=list)
    do_not_contact_lead_ids: List[int] = Field(default_factory=list)


class CamSafetySettingsOut(CamSafetySettings):
    """Safety settings response with usage stats."""
    id: Optional[int] = None
    current_usage: Optional[dict] = None  # Today's usage per channel
    
    model_config = ConfigDict(from_attributes=True)
