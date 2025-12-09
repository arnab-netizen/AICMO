"""
CAM domain models (Pydantic).

Phase CAM-0: Pure domain models with no side effects or database dependencies.
Phase CAM-1: Extended with lead acquisition fields (lead_score, tags, next_action_at, etc.)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
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


class CampaignMode(str, Enum):
    """
    Campaign execution mode (Phase 10: Simulation).
    
    SIMULATION: Test mode, no real emails sent, records simulated events
    LIVE: Production mode, real emails sent to prospects
    """
    
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class Campaign(AicmoBaseModel):
    """
    Outreach campaign targeting a specific niche or audience.
    
    Groups leads together for coordinated messaging and tracking.
    Phase CAM-1: Extended with lead acquisition fields.
    Phase 8-10: Added reply tracking, review fields, simulation mode.
    """
    
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    target_niche: Optional[str] = None
    active: bool = True
    
    # Phase CAM-1: Lead acquisition parameters
    service_key: Optional[str] = None  # e.g. "web_design", "seo", "social_media"
    target_clients: Optional[int] = None  # goal number of leads to acquire
    target_mrr: Optional[float] = None  # target monthly recurring revenue
    channels_enabled: List[str] = ["email"]  # e.g. ["email", "linkedin"]
    max_emails_per_day: Optional[int] = None  # per-campaign daily limit
    max_outreach_per_day: Optional[int] = None
    
    # Phase 10: Simulation mode
    mode: CampaignMode = CampaignMode.LIVE  # SIMULATION or LIVE


class Lead(AicmoBaseModel):
    """
    Individual prospect or lead for client acquisition.
    
    Contains contact information and enrichment data for personalized outreach.
    Phase CAM-1: Extended with lead scoring and timing fields.
    Phase 8-10: Added reply tracking, human review fields.
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
    
    # Phase CAM-1: Lead scoring and profiling
    lead_score: Optional[float] = None  # 0.0-1.0, higher = better fit
    tags: List[str] = []  # e.g. ["hot", "warm", "cold", "decision_maker"]
    enrichment_data: Optional[Dict[str, Any]] = None  # From Apollo, Dropcontact, etc.
    
    # Phase CAM-1: Timing and follow-up
    last_contacted_at: Optional[datetime] = None
    next_action_at: Optional[datetime] = None  # When to attempt next contact
    last_reply_at: Optional[datetime] = None

    notes: Optional[str] = None
    
    # Phase 9: Human review queue
    requires_human_review: bool = False  # Pause auto actions, needs human approval
    review_type: Optional[str] = None  # e.g. "MESSAGE", "PROPOSAL", "PRICING"
    review_reason: Optional[str] = None  # Why human review is needed


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
