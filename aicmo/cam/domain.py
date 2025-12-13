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
    ROUTED = "ROUTED"  # Phase 5: Routed to sequence
    LOST = "LOST"
    MANUAL_REVIEW = "MANUAL_REVIEW"  # Phase 4: Requires manual qualification


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


class CompanySize(str, Enum):
    """Company size category (Phase A)."""
    
    EARLY_STAGE = "early_stage"      # < 10 employees
    MID_MARKET = "mid_market"        # 10-500 employees
    ENTERPRISE = "enterprise"        # 500+ employees


class LeadGrade(str, Enum):
    """
    Lead quality grade (Phase A).
    
    A: Hot lead - high fit, budget, timeline
    B: Warm lead - good fit, some buying signals
    C: Cool lead - potential, needs nurturing
    D: Cold lead - low fit, early stage
    """
    
    A = "A"
    B = "B"
    C = "C"
    D = "D"


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
    Phase A: Added CRM fields (company info, decision maker, budget, timeline, grading).
    """
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None

    # Basic contact information
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
    
    # Phase 5: Lead Routing
    routing_sequence: Optional[str] = None  # e.g. "aggressive_close", "regular_nurture"
    sequence_start_at: Optional[datetime] = None  # When sequence started
    
    # Phase 6: Lead Nurture
    engagement_notes: Optional[str] = None  # Notes from engagement tracking
    first_name: Optional[str] = None  # First name for personalization
    title: Optional[str] = None  # Job title for personalization
    
    # Phase 9: Human review queue
    requires_human_review: bool = False  # Pause auto actions, needs human approval
    review_type: Optional[str] = None  # e.g. "MESSAGE", "PROPOSAL", "PRICING"
    review_reason: Optional[str] = None  # Why human review is needed

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Company Information
    # ═══════════════════════════════════════════════════════════════════
    company_size: Optional[str] = None  # CompanySize enum value
    industry: Optional[str] = None
    growth_rate: Optional[str] = None  # e.g., "10-20%"
    annual_revenue: Optional[str] = None  # e.g., "$1M-$5M"
    employee_count: Optional[int] = None
    company_website: Optional[str] = None
    company_headquarters: Optional[str] = None
    founding_year: Optional[int] = None
    funding_status: Optional[str] = None  # e.g., "bootstrapped", "funded"

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Decision Maker
    # ═══════════════════════════════════════════════════════════════════
    decision_maker_name: Optional[str] = None
    decision_maker_email: Optional[str] = None
    decision_maker_role: Optional[str] = None
    decision_maker_linkedin: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Sales Information
    # ═══════════════════════════════════════════════════════════════════
    budget_estimate_range: Optional[str] = None  # e.g., "$10K-$50K"
    timeline_months: Optional[int] = None
    pain_points: Optional[List[str]] = None  # JSON array of strings
    buying_signals: Optional[Dict[str, Any]] = None  # JSON object with signal data

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Lead Grading
    # ═══════════════════════════════════════════════════════════════════
    lead_grade: Optional[str] = None  # LeadGrade enum value (A/B/C/D)
    conversion_probability: Optional[float] = None  # 0.0-1.0
    fit_score_for_service: Optional[float] = None  # 0.0-1.0
    graded_at: Optional[datetime] = None
    grade_reason: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Tracking
    # ═══════════════════════════════════════════════════════════════════
    proposal_generated_at: Optional[datetime] = None
    proposal_content_id: Optional[str] = None
    contract_signed_at: Optional[datetime] = None
    referral_source: Optional[str] = None
    referred_by_name: Optional[str] = None

    # ═══════════════════════════════════════════════════════════════════
    # PHASE D: LEAD ACQUISITION SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    # Phase 4: Lead Qualification
    qualification_notes: Optional[str] = None  # Reason for qualification status
    email_valid: Optional[bool] = None  # Is email valid/deliverable
    intent_signals: Optional[Dict[str, Any]] = None  # Intent signal data
    
    # Phase 5: Lead Routing
    routing_sequence: Optional[str] = None  # ContentSequenceType (aggressive_close, regular_nurture, etc.)
    sequence_start_at: Optional[datetime] = None  # When sequence began
    engagement_notes: Optional[str] = None  # Engagement tracking notes


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

# ═══════════════════════════════════════════════════════════════════
# PHASE B: OUTREACH CHANNELS
# ═══════════════════════════════════════════════════════════════════

class ChannelType(str, Enum):
    """
    Channel type for outreach attempts.
    
    Phase B: Support for multi-channel outreach coordination.
    """
    
    EMAIL = "email"
    LINKEDIN = "linkedin"
    CONTACT_FORM = "contact_form"
    PHONE = "phone"


class OutreachStatus(str, Enum):
    """
    Status of an outreach attempt across channels.
    
    Phase B: Tracks progression through multi-channel sequence.
    """
    
    PENDING = "PENDING"        # Scheduled but not yet attempted
    SENT = "SENT"              # Successfully sent/submitted
    DELIVERED = "DELIVERED"    # Reached recipient (email opened, LinkedIn read)
    REPLIED = "REPLIED"        # Recipient replied/engaged
    BOUNCED = "BOUNCED"        # Hard bounce (invalid email, unreachable LinkedIn)
    FAILED = "FAILED"          # Soft failure (retry eligible)
    SKIPPED = "SKIPPED"        # Skipped (due to sequencing logic)


class LinkedInConnectionStatus(str, Enum):
    """LinkedIn connection status for a lead."""
    
    NOT_CONNECTED = "not_connected"       # No connection
    CONNECTION_REQUESTED = "connection_requested"  # Pending request
    CONNECTED = "connected"                 # Connected
    BLOCKED = "blocked"                     # Blocked by LinkedIn


class OutreachMessage(AicmoBaseModel):
    """
    Message content and metadata for outreach.
    
    Can be used across different channels with appropriate templating.
    """
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    lead_id: Optional[int] = None
    
    channel: ChannelType
    message_type: str  # e.g. "intro", "follow_up", "proposal"
    
    # Content
    subject: Optional[str] = None  # For email
    body: str
    personalization_data: Optional[Dict[str, Any]] = None  # For template rendering
    
    # Metadata
    template_name: Optional[str] = None
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    # Tracking
    status: OutreachStatus = OutreachStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # LinkedIn specific
    linkedin_message_id: Optional[str] = None
    
    # Email specific
    email_message_id: Optional[str] = None
    
    # Contact form specific
    form_url: Optional[str] = None
    form_submission_id: Optional[str] = None


class ChannelConfig(AicmoBaseModel):
    """
    Configuration for a specific channel in a campaign.
    
    Defines rate limits, retry policies, and templates for a channel.
    """
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    
    channel: ChannelType
    enabled: bool = True
    
    # Rate limiting
    max_per_day: Optional[int] = None  # Max attempts per day
    max_per_hour: Optional[int] = None
    max_per_lead: Optional[int] = None  # Max per individual lead
    cooldown_hours: int = 24  # Hours between channel attempts on same lead
    
    # Retry policy
    max_retries: int = 2
    retry_backoff_hours: List[int] = [24, 48]  # Retry delays
    
    # Templates
    default_template: Optional[str] = None
    templates: Optional[Dict[str, str]] = None  # message_type -> template_name
    
    # Channel-specific settings
    settings: Optional[Dict[str, Any]] = None  # JSON for channel-specific configs
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SequenceStep(AicmoBaseModel):
    """
    Single step in a multi-channel outreach sequence.
    """
    
    id: Optional[int] = None
    sequence_id: Optional[int] = None
    
    order: int  # Step order in sequence
    channel: ChannelType
    
    # Conditions
    condition: Optional[str] = None  # e.g. "if email_failed", "after_wait_24h"
    wait_hours: int = 0  # Wait before attempting this step
    
    # Message
    message_template: str  # Template name to use
    personalization_enabled: bool = True
    
    # Retry policy
    max_retries: int = 2
    retry_delay_hours: int = 24
    
    # Action on success/failure
    on_success: Optional[str] = None  # Next action if successful
    on_failure: Optional[str] = None  # Next action if failed (e.g. "next_step", "retry")


class SequenceConfig(AicmoBaseModel):
    """
    Multi-channel outreach sequence definition.
    
    Defines the flow: try email, if fails try LinkedIn, if fails try form, etc.
    """
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    
    name: str
    description: Optional[str] = None
    
    # Sequence steps
    steps: List[SequenceStep] = []
    
    # Configuration
    enabled: bool = True
    default_for_campaign: bool = False
    
    # Global settings
    max_total_attempts_per_lead: int = 10
    sequence_timeout_days: int = 30  # Give up after 30 days
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════
# PHASE C: ANALYTICS & REPORTING
# ═══════════════════════════════════════════════════════════════════

class MetricsPeriod(str, Enum):
    """Time period for metrics aggregation."""
    
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AttributionModel(str, Enum):
    """Attribution model for multi-touch attribution."""
    
    FIRST_TOUCH = "first_touch"        # Credit first channel
    LAST_TOUCH = "last_touch"          # Credit last channel
    LINEAR = "linear"                  # Equal credit all channels
    TIME_DECAY = "time_decay"          # More credit to recent channels
    POSITION_BASED = "position_based"  # 40%-40%-20% first-last-middle


class ABTestType(str, Enum):
    """Type of A/B test."""
    
    MESSAGE = "message"              # Subject, body, template
    CHANNEL = "channel"              # Email vs LinkedIn priority
    TIMING = "timing"                # Send time optimization
    SEGMENT = "segment"              # Different audience segments
    TEMPLATE = "template"            # Template A vs B


class ABTestStatus(str, Enum):
    """Status of an A/B test."""
    
    DRAFT = "draft"                  # Not yet started
    RUNNING = "running"              # Currently running
    PAUSED = "paused"                # Paused
    COMPLETED = "completed"          # Finished
    CONCLUDED = "concluded"          # Results analyzed


class CampaignMetrics(AicmoBaseModel):
    """
    Aggregated metrics for a campaign.
    
    Snapshot of campaign performance at a point in time.
    """
    
    id: Optional[int] = None
    campaign_id: int
    metric_date: datetime
    
    # Counts
    total_leads: int = 0
    engaged_leads: int = 0
    replied_leads: int = 0
    converted_leads: int = 0
    
    # Rates
    engagement_rate: float = 0.0  # engaged / total
    reply_rate: float = 0.0       # replied / total
    conversion_rate: float = 0.0  # converted / total
    
    # Costs & ROI
    total_spend: Optional[float] = None
    cost_per_lead: Optional[float] = None
    cost_per_conversion: Optional[float] = None
    revenue_generated: Optional[float] = None
    net_roi: Optional[float] = None
    roi_percent: Optional[float] = None
    
    # Trends (vs previous period)
    lead_velocity: int = 0         # leads/day
    wow_growth: Optional[float] = None  # Week-over-week %
    mom_growth: Optional[float] = None  # Month-over-month %
    
    # Metadata
    period: MetricsPeriod = MetricsPeriod.DAILY
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChannelMetrics(AicmoBaseModel):
    """
    Performance metrics for a specific channel.
    
    Broken down by channel type (EMAIL, LINKEDIN, CONTACT_FORM).
    """
    
    id: Optional[int] = None
    campaign_id: int
    channel: ChannelType
    metric_date: datetime
    
    # Counts
    sent_count: int = 0
    delivered_count: int = 0
    replied_count: int = 0
    bounced_count: int = 0
    
    # Rates
    delivery_rate: float = 0.0  # delivered / sent
    reply_rate: float = 0.0     # replied / delivered
    bounce_rate: float = 0.0    # bounced / sent
    
    # Costs
    cost_per_send: Optional[float] = None
    cost_per_delivery: Optional[float] = None
    cost_per_reply: Optional[float] = None
    
    # Efficiency
    efficiency_score: float = 0.0  # Composite score 0-100
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LeadAttribution(AicmoBaseModel):
    """
    Attribution tracking for a lead across channels.
    
    Tracks which channels contributed to lead conversion.
    """
    
    id: Optional[int] = None
    lead_id: int
    campaign_id: int
    
    # Touch points
    first_touch_channel: Optional[ChannelType] = None
    last_touch_channel: Optional[ChannelType] = None
    conversion_channel: Optional[ChannelType] = None
    
    # Multi-touch attribution
    attribution_model: AttributionModel = AttributionModel.LAST_TOUCH
    attribution_weights: Optional[Dict[str, float]] = None  # channel -> weight
    
    # Timeline
    first_contact_at: Optional[datetime] = None
    last_contact_at: Optional[datetime] = None
    conversion_at: Optional[datetime] = None
    touch_count: int = 0
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ABTestConfig(AicmoBaseModel):
    """
    Configuration for an A/B test.
    
    Defines hypothesis, test groups, and statistical requirements.
    """
    
    id: Optional[int] = None
    campaign_id: int
    
    name: str
    hypothesis: str
    
    test_type: ABTestType
    start_date: datetime
    end_date: Optional[datetime] = None
    
    # Test groups (control vs variant(s))
    control_group: Optional[Dict[str, Any]] = None   # {message: "...", template: "..."}
    variant_group: Optional[Dict[str, Any]] = None   # {message: "...", template: "..."}
    additional_variants: Optional[List[Dict[str, Any]]] = None
    
    # Statistical requirements
    sample_size: int = 100
    confidence_level: float = 0.95  # 95%
    statistical_power: float = 0.80  # 80%
    
    # Status
    status: ABTestStatus = ABTestStatus.DRAFT
    actual_sample_size: Optional[int] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ABTestResult(AicmoBaseModel):
    """
    Results and statistical analysis of an A/B test.
    
    Contains metrics and statistical significance calculations.
    """
    
    id: Optional[int] = None
    test_id: int
    
    # Group metrics
    control_metrics: Optional[Dict[str, float]] = None  # {conversion_rate: 0.15, ...}
    variant_metrics: Optional[Dict[str, float]] = None  # {conversion_rate: 0.18, ...}
    
    # Statistical analysis
    p_value: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None  # {lower: 0.02, upper: 0.04}
    statistical_significance: Optional[bool] = None  # p < 0.05
    effect_size: Optional[float] = None
    
    # Winner determination
    winner: Optional[str] = None  # "control", "variant", "inconclusive"
    confidence: Optional[float] = None  # Confidence in result
    
    # Recommendations
    recommendation: Optional[str] = None
    estimated_impact: Optional[Dict[str, float]] = None  # Impact projections
    
    # Metadata
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ROICalculation(AicmoBaseModel):
    """
    ROI tracking for a lead across the entire campaign.
    
    Tracks acquisition cost and revenue to calculate ROI.
    """
    
    id: Optional[int] = None
    lead_id: int
    campaign_id: int
    
    # Cost tracking
    acquisition_cost: float = 0.0
    channel_costs: Optional[Dict[str, float]] = None  # {EMAIL: 0.05, LINKEDIN: 0.10}
    total_cost: float = 0.0
    
    # Revenue tracking
    deal_value: Optional[float] = None
    deal_stage: Optional[str] = None  # "won", "lost", "pipeline"
    close_probability: float = 0.0
    expected_revenue: Optional[float] = None
    
    # ROI calculation
    roi: Optional[float] = None          # (revenue - cost) / cost
    roi_percent: Optional[float] = None  # ROI as percentage
    payback_period_days: Optional[int] = None
    
    # Metadata
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnalyticsEvent(AicmoBaseModel):
    """
    Raw event for analytics tracking.
    
    Used for debugging and real-time analytics.
    """
    
    id: Optional[int] = None
    
    event_type: str  # "send", "open", "reply", "convert"
    lead_id: int
    campaign_id: int
    channel: Optional[ChannelType] = None
    
    # Flexible event data
    event_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: Optional[datetime] = None