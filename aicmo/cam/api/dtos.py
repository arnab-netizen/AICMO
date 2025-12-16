"""
CAM (Client Acquisition) - Data Transfer Objects.

DTOs are use-case shaped, not DB shaped.
Decoupled from internal ORM models.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from aicmo.shared.ids import LeadId, CampaignId, ClientId


class RawLeadDTO(BaseModel):
    """Raw lead data from external source (pre-qualification)."""
    
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    source: str  # e.g., "linkedin", "manual", "csv_import"
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class LeadDTO(BaseModel):
    """Enriched lead after ingestion."""
    
    lead_id: LeadId
    campaign_id: CampaignId
    name: str
    email: str
    company: Optional[str] = None
    title: Optional[str] = None
    source: str
    status: str  # "NEW", "QUALIFIED", "CONTACTED", "ENGAGED", etc.
    created_at: datetime
    updated_at: datetime


class LeadScoreDTO(BaseModel):
    """Lead scoring result."""
    
    lead_id: LeadId
    score: float  # 0.0 - 1.0
    grade: str  # "A", "B", "C", "D", "F"
    reasons: List[str]  # Why this score?
    scored_at: datetime


class QualifiedLeadDTO(BaseModel):
    """Lead after qualification (includes score/grade)."""
    
    lead: LeadDTO
    score: LeadScoreDTO
    is_qualified: bool
    qualification_reasons: List[str]


class OutreachMessageDTO(BaseModel):
    """Single outreach message (email, LinkedIn, etc)."""
    
    channel: str  # "email", "linkedin", "contact_form"
    subject: Optional[str] = None
    body: str
    personalization_tokens: Dict[str, str] = Field(default_factory=dict)


class OutreachPlanDTO(BaseModel):
    """Multi-channel outreach plan for a lead."""
    
    lead_id: LeadId
    messages: List[OutreachMessageDTO]
    sequence_config: Dict[str, Any]  # Timing, fallback rules, etc.
    created_at: datetime


class SignedClientDTO(BaseModel):
    """Newly signed client (converted from lead)."""
    
    client_id: ClientId
    original_lead_id: LeadId
    name: str
    email: str
    company: Optional[str] = None
    signed_at: datetime
    contract_value: Optional[float] = None


class LeadSummaryDTO(BaseModel):
    """Lightweight lead summary for list views."""
    
    lead_id: LeadId
    name: str
    company: Optional[str] = None
    status: str
    grade: Optional[str] = None
    created_at: datetime


class LeadStatusDTO(BaseModel):
    """Lead status snapshot."""
    
    lead_id: LeadId
    status: str
    last_contact_at: Optional[datetime] = None
    next_action: Optional[str] = None


class CampaignCreateDTO(BaseModel):
    """Input for creating a campaign."""
    
    client_id: ClientId
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class CampaignDTO(BaseModel):
    """Campaign details."""
    
    campaign_id: CampaignId
    client_id: ClientId
    name: str
    status: str  # "ACTIVE", "PAUSED", "COMPLETED"
    created_at: datetime
    config: Dict[str, Any] = Field(default_factory=dict)


class CampaignStatusDTO(BaseModel):
    """Campaign status summary."""
    
    campaign_id: CampaignId
    status: str
    total_leads: int
    active_leads: int
    last_updated: datetime


__all__ = [
    "RawLeadDTO",
    "LeadDTO",
    "LeadScoreDTO",
    "QualifiedLeadDTO",
    "OutreachMessageDTO",
    "OutreachPlanDTO",
    "SignedClientDTO",
    "LeadSummaryDTO",
    "LeadStatusDTO",
    "CampaignCreateDTO",
    "CampaignDTO",
    "CampaignStatusDTO",
]
