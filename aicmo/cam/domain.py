"""
CAM domain models (Pydantic).

Phase CAM-0: Pure domain models with no side effects or database dependencies.
"""

from typing import Optional
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class LeadSource(str, Enum):
    """Source where the lead was acquired from."""
    
    CSV = "csv"
    APOLLO = "apollo"
    MANUAL = "manual"
    OTHER = "other"


class LeadStatus(str, Enum):
    """Current status of a lead in the acquisition funnel."""
    
    NEW = "NEW"
    ENRICHED = "ENRICHED"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    QUALIFIED = "QUALIFIED"
    LOST = "LOST"


class Channel(str, Enum):
    """Communication channel for outreach."""
    
    LINKEDIN = "linkedin"
    EMAIL = "email"
    OTHER = "other"


class Campaign(AicmoBaseModel):
    """
    Outreach campaign targeting a specific niche or audience.
    
    Groups leads together for coordinated messaging and tracking.
    """
    
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    target_niche: Optional[str] = None
    active: bool = True


class Lead(AicmoBaseModel):
    """
    Individual prospect or lead for client acquisition.
    
    Contains contact information and enrichment data for personalized outreach.
    """
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None

    name: str
    company: Optional[str] = None
    role: Optional[str] = None

    email: Optional[str] = None
    linkedin_url: Optional[str] = None

    source: LeadSource = LeadSource.OTHER
    status: LeadStatus = LeadStatus.NEW

    notes: Optional[str] = None


class SequenceStep(AicmoBaseModel):
    """
    Single step in a multi-touch outreach sequence.
    
    Defines the channel, message template, and timing for one touchpoint.
    """
    
    step_number: int
    channel: Channel
    template: str  # e.g. "{first_name}, saw your work on {platform}..."
    delay_days: int = 0


class OutreachMessage(AicmoBaseModel):
    """
    Generated outreach message ready to send to a lead.
    
    Contains fully personalized content based on lead data and campaign context.
    """
    
    lead: Lead
    campaign: Campaign
    channel: Channel

    step_number: int
    subject: Optional[str] = None
    body: str


class AttemptStatus(str, Enum):
    """Status of an outreach attempt."""
    
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class OutreachAttempt(AicmoBaseModel):
    """
    Record of a single outreach attempt to a lead.
    
    Tracks execution status, errors, and timing for analytics and follow-up scheduling.
    """
    
    id: Optional[int] = None
    lead_id: int
    campaign_id: int
    channel: Channel
    step_number: int

    status: AttemptStatus = AttemptStatus.PENDING
    last_error: Optional[str] = None
