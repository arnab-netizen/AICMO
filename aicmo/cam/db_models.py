"""
CAM database models (SQLAlchemy).

Phase CAM-1: Persistent storage for campaigns, leads, and outreach attempts.
Phase CAM-7: Discovery jobs and discovered profiles for ethical lead finding.
"""

from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Float,
    Enum as SAEnum,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.sql import func

from aicmo.core.db import Base
from aicmo.cam.domain import LeadSource, LeadStatus, Channel, AttemptStatus, CampaignMode


class CampaignDB(Base):
    """
    Outreach campaign database model.
    
    Groups leads together for coordinated messaging and tracking.
    Phase 9.1: Added strategy document storage and status tracking.
    Stage 1: Added project_state for formal Project ↔ Campaign mapping.
    """
    
    __tablename__ = "cam_campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    target_niche = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    # Project state tracking (Stage 1)
    project_state = Column(String, nullable=True, default="STRATEGY_DRAFT")
    
    # Strategy document storage (Phase 9.1)
    strategy_text = Column(Text, nullable=True)
    strategy_status = Column(String, nullable=True, default="DRAFT")  # DRAFT, APPROVED, REJECTED
    strategy_rejection_reason = Column(Text, nullable=True)
    
    # Intake context (Phase 9.1)
    intake_goal = Column(Text, nullable=True)
    intake_constraints = Column(Text, nullable=True)
    intake_audience = Column(Text, nullable=True)
    intake_budget = Column(String, nullable=True)
    
    # Phase CAM-1: Lead acquisition parameters
    service_key = Column(String, nullable=True)  # e.g. "web_design", "seo"
    target_clients = Column(Integer, nullable=True)  # goal number of leads
    target_mrr = Column(Float, nullable=True)  # target monthly recurring revenue
    channels_enabled = Column(JSON, nullable=False, default=["email"])  # list of enabled channels
    max_emails_per_day = Column(Integer, nullable=True)  # per-campaign daily limit
    max_outreach_per_day = Column(Integer, nullable=True)
    
    # Phase 10: Simulation mode
    mode = Column(SAEnum(CampaignMode), nullable=False, default=CampaignMode.LIVE)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class LeadDB(Base):
    """
    Lead/prospect database model.
    
    Stores contact information and enrichment data for personalized outreach.
    Phase CAM-1: Extended with lead scoring and timing fields.
    """
    
    __tablename__ = "cam_leads"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True)

    name = Column(String, nullable=False)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)

    email = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)

    source = Column(SAEnum(LeadSource), nullable=False, default=LeadSource.OTHER)
    status = Column(SAEnum(LeadStatus), nullable=False, default=LeadStatus.NEW)
    
    # Phase 8: Pipeline stage
    stage = Column(String, nullable=False, default="NEW")
    
    # Phase CAM-1: Lead scoring and profiling
    lead_score = Column(Float, nullable=True)  # 0.0-1.0, higher = better fit
    tags = Column(JSON, nullable=False, default=[])  # e.g. ["hot", "warm", "cold"]
    enrichment_data = Column(JSON, nullable=True)  # From Apollo, Dropcontact, etc.
    
    # Phase CAM-1: Timing and follow-up
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)
    next_action_at = Column(DateTime(timezone=True), nullable=True)  # When to attempt next contact
    last_replied_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    
    # Phase 5: Lead Routing
    routing_sequence = Column(String, nullable=True)  # e.g. "aggressive_close", "regular_nurture"
    sequence_start_at = Column(DateTime(timezone=True), nullable=True)  # When sequence started
    
    # Phase 6: Lead Nurture
    engagement_notes = Column(Text, nullable=True)  # Notes from engagement tracking
    first_name = Column(String, nullable=True)  # First name for personalization
    title = Column(String, nullable=True)  # Job title for personalization
    
    # Phase 9: Human review queue
    requires_human_review = Column(Boolean, nullable=False, default=False)
    review_type = Column(String, nullable=True)  # e.g. "MESSAGE", "PROPOSAL", "PRICING"
    review_reason = Column(Text, nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Company Information
    # ═══════════════════════════════════════════════════════════════════
    company_size = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    growth_rate = Column(String, nullable=True)
    annual_revenue = Column(String, nullable=True)
    employee_count = Column(Integer, nullable=True)
    company_website = Column(String, nullable=True)
    company_headquarters = Column(String, nullable=True)
    founding_year = Column(Integer, nullable=True)
    funding_status = Column(String, nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Decision Maker
    # ═══════════════════════════════════════════════════════════════════
    decision_maker_name = Column(String, nullable=True)
    decision_maker_email = Column(String, nullable=True)
    decision_maker_role = Column(String, nullable=True)
    decision_maker_linkedin = Column(String, nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Sales Information
    # ═══════════════════════════════════════════════════════════════════
    budget_estimate_range = Column(String, nullable=True)
    timeline_months = Column(Integer, nullable=True)
    pain_points = Column(JSON, nullable=True)
    buying_signals = Column(JSON, nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Lead Grading
    # ═══════════════════════════════════════════════════════════════════
    lead_grade = Column(String, nullable=True, default="D")
    conversion_probability = Column(Float, nullable=True, default=0.0)
    fit_score_for_service = Column(Float, nullable=True, default=0.0)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    grade_reason = Column(String, nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A: CRM FIELDS - Tracking
    # ═══════════════════════════════════════════════════════════════════
    proposal_generated_at = Column(DateTime(timezone=True), nullable=True)
    proposal_content_id = Column(String, nullable=True)
    contract_signed_at = Column(DateTime(timezone=True), nullable=True)
    referral_source = Column(String, nullable=True)
    referred_by_name = Column(String, nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE B: OUTREACH CHANNELS
    # ═══════════════════════════════════════════════════════════════════
    linkedin_status = Column(String, nullable=True, default="not_connected")  # not_connected, connection_requested, connected, blocked
    contact_form_url = Column(String, nullable=True)  # URL of company's contact form
    contact_form_last_submitted_at = Column(DateTime(timezone=True), nullable=True)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE D: LEAD ACQUISITION SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    # Phase 4: Lead Qualification
    qualification_notes = Column(Text, nullable=True)  # Reason for qualification status
    email_valid = Column(Boolean, nullable=True)  # Is email valid/deliverable
    intent_signals = Column(JSON, nullable=True)  # Intent signal data
    
    # Phase 5: Lead Routing
    routing_sequence = Column(String, nullable=True)  # ContentSequenceType (aggressive_close, regular_nurture, etc.)
    sequence_start_at = Column(DateTime(timezone=True), nullable=True)  # When sequence began
    engagement_notes = Column(Text, nullable=True)  # Engagement tracking notes

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Indexes for efficient querying (Phase A)
    __table_args__ = (
        Index('idx_lead_grade', 'lead_grade'),
        Index('idx_conversion_probability', 'conversion_probability'),
        Index('idx_fit_score_for_service', 'fit_score_for_service'),
    )


class OutreachAttemptDB(Base):
    """
    Outreach attempt database model.
    
    Tracks execution status, errors, and timing for analytics and follow-up scheduling.
    Phase B: Extended with channel sequencing and retry tracking.
    """
    
    __tablename__ = "cam_outreach_attempts"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    channel = Column(SAEnum(Channel), nullable=False)
    step_number = Column(Integer, nullable=False)

    status = Column(SAEnum(AttemptStatus), nullable=False, default=AttemptStatus.PENDING)
    last_error = Column(Text, nullable=True)
    
    # Phase B: Retry tracking for channel sequencing
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=2)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DiscoveryJobDB(Base):
    """
    Discovery job database model (Phase 7).
    
    Tracks lead discovery operations across platforms.
    """
    
    __tablename__ = "cam_discovery_jobs"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    criteria = Column(JSON, nullable=False)  # Serialized DiscoveryCriteria
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True)
    
    status = Column(String, nullable=False, default="PENDING")  # PENDING/RUNNING/DONE/FAILED
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class DiscoveredProfileDB(Base):
    """
    Discovered profile database model (Phase 7).
    
    Stores profiles found during discovery jobs before conversion to leads.
    """
    
    __tablename__ = "cam_discovered_profiles"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("cam_discovery_jobs.id"), nullable=False)
    
    platform = Column(String, nullable=False)  # linkedin/twitter/instagram/web
    handle = Column(String, nullable=False)
    profile_url = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    
    bio = Column(Text, nullable=True)
    followers = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    match_score = Column(Float, nullable=False, default=0.5)
    
    discovered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ContactEventDB(Base):
    """
    Contact event database model (Phase 8).
    
    Tracks interactions with leads (replies, calls, meetings).
    """
    
    __tablename__ = "cam_contact_events"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False)
    
    channel = Column(String, nullable=False)  # linkedin/email/other
    direction = Column(String, nullable=False)  # OUTBOUND/INBOUND
    summary = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AppointmentDB(Base):
    """
    Appointment database model (Phase 8).
    
    Tracks scheduled meetings with leads.
    """
    
    __tablename__ = "cam_appointments"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False)
    
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)
    location = Column(String, nullable=True)
    calendar_link = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="SCHEDULED")  # SCHEDULED/COMPLETED/CANCELLED
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SafetySettingsDB(Base):
    """
    Safety and compliance settings (singleton table).
    
    Phase 9: Stores rate limits, send windows, and DNC lists.
    Phase 9.1: Added system pause flag for Command Center.
    """
    
    __tablename__ = "cam_safety_settings"

    id = Column(Integer, primary_key=True)
    data = Column(JSON, nullable=False)  # Serialized SafetySettings
    system_paused = Column(Boolean, nullable=False, default=False)  # Phase 9.1: Global pause control
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class CreativeAssetDB(Base):
    """
    Persistent storage for generated creative assets.
    
    Stage 2: Links CreativeVariants to campaigns with publish status tracking.
    Enables asset library management and execution pipeline integration.
    """
    
    __tablename__ = "creative_assets"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    
    # Creative content
    platform = Column(String, nullable=False)  # "instagram", "linkedin", "twitter"
    format = Column(String, nullable=False)  # "reel", "post", "carousel", "thread"
    hook = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    cta = Column(String, nullable=True)
    tone = Column(String, nullable=True)  # "professional", "friendly", "bold"
    
    # Publishing tracking
    publish_status = Column(String, nullable=False, default="DRAFT")  # DRAFT, APPROVED, SCHEDULED, PUBLISHED
    scheduled_date = Column(String, nullable=True)  # ISO date string
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    meta = Column(JSON, nullable=True)  # Additional creative metadata
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ExecutionJobDB(Base):
    """
    Persistent storage for execution jobs.
    
    Stage 3: Tracks social posts and other content delivery jobs
    through the execution pipeline from QUEUED → DONE.
    """
    
    __tablename__ = "execution_jobs"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    creative_id = Column(Integer, ForeignKey("creative_assets.id"), nullable=True)
    
    # Job details
    job_type = Column(String, nullable=False)  # "social_post", "email", "crm_sync"
    platform = Column(String, nullable=False)  # "instagram", "linkedin", "twitter", "email"
    payload = Column(JSON, nullable=False)  # ContentItem or job-specific data
    
    # Execution tracking
    status = Column(String, nullable=False, default="QUEUED")  # QUEUED, IN_PROGRESS, DONE, FAILED
    retries = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    # Results
    external_id = Column(String, nullable=True)  # Platform's post/job ID
    last_error = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ═══════════════════════════════════════════════════════════════════
# PHASE B: OUTREACH CHANNELS
# ═══════════════════════════════════════════════════════════════════

class ChannelConfigDB(Base):
    """
    Channel configuration for a campaign.
    
    Stores settings for each outreach channel (email, LinkedIn, contact form).
    Phase B: Multi-channel outreach support.
    """
    
    __tablename__ = "cam_channel_configs"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    
    # Channel type
    channel = Column(String, nullable=False)  # email, linkedin, contact_form, phone
    enabled = Column(Boolean, nullable=False, default=True)
    
    # Rate limiting
    max_per_day = Column(Integer, nullable=True)
    max_per_hour = Column(Integer, nullable=True)
    max_per_lead = Column(Integer, nullable=True)
    cooldown_hours = Column(Integer, nullable=False, default=24)
    
    # Retry policy
    max_retries = Column(Integer, nullable=False, default=2)
    retry_backoff_hours = Column(JSON, nullable=False, default=[24, 48])
    
    # Templates
    default_template = Column(String, nullable=True)
    templates = Column(JSON, nullable=True)  # message_type -> template_name
    
    # Channel-specific settings
    settings = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SequenceConfigDB(Base):
    """
    Multi-channel outreach sequence configuration.
    
    Defines a sequence of outreach attempts across different channels.
    Phase B: Channel sequencing (email -> LinkedIn -> form, etc.)
    """
    
    __tablename__ = "cam_sequence_configs"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    
    # Sequence metadata
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    enabled = Column(Boolean, nullable=False, default=True)
    default_for_campaign = Column(Boolean, nullable=False, default=False)
    
    # Global settings
    max_total_attempts_per_lead = Column(Integer, nullable=False, default=10)
    sequence_timeout_days = Column(Integer, nullable=False, default=30)
    
    # Steps (JSON for flexibility)
    steps = Column(JSON, nullable=False, default=[])
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class OutreachMessageDB(Base):
    """
    Individual outreach message record.
    
    Tracks all outreach attempts with channel, status, and content.
    Phase B: Message history across channels.
    """
    
    __tablename__ = "cam_outreach_messages"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False)
    
    # Channel and message info
    channel = Column(String, nullable=False)  # email, linkedin, contact_form, phone
    message_type = Column(String, nullable=False)  # intro, follow_up, proposal
    
    # Content
    subject = Column(String, nullable=True)  # For email
    body = Column(Text, nullable=False)
    template_name = Column(String, nullable=True)
    
    # Status
    status = Column(String, nullable=False, default="PENDING")  # PENDING, SENT, DELIVERED, REPLIED, FAILED
    
    # Retry tracking
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Channel-specific IDs
    email_message_id = Column(String, nullable=True)
    linkedin_message_id = Column(String, nullable=True)
    form_submission_id = Column(String, nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Index for fast queries
    __table_args__ = (
        Index('idx_outreach_lead_channel', 'lead_id', 'channel'),
        Index('idx_outreach_status', 'status'),
        Index('idx_outreach_campaign', 'campaign_id'),
    )


# ============================================================================
# PHASE C: ANALYTICS & REPORTING - DATABASE MODELS
# ============================================================================
# Purpose: Track campaign metrics, channel performance, attribution, A/B tests,
# ROI, and raw analytics events for data-driven decision making.
# ============================================================================

class CampaignMetricsDB(Base):
    """Campaign-level aggregated metrics and performance indicators."""
    __tablename__ = 'campaign_metrics'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=False, index=True)
    
    # Time aggregation
    period = Column(String, nullable=False)  # DAILY, WEEKLY, MONTHLY, etc.
    date = Column(Date, nullable=False, index=True)
    
    # Lead metrics
    total_leads = Column(Integer, default=0)
    qualified_leads = Column(Integer, default=0)
    engaged_leads = Column(Integer, default=0)
    converted_leads = Column(Integer, default=0)
    
    # Engagement metrics
    sent_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    
    # Performance calculations
    engagement_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, nullable=True)  # hours
    
    # Revenue metrics
    total_cost = Column(Float, default=0.0)
    total_revenue = Column(Float, nullable=True)
    roi_percent = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_campaign_metrics_campaign_date', 'campaign_id', 'date'),
        Index('idx_campaign_metrics_period', 'campaign_id', 'period'),
    )


class ChannelMetricsDB(Base):
    """Per-channel performance metrics and effectiveness tracking."""
    __tablename__ = 'channel_metrics'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=False, index=True)
    
    # Channel identifier
    channel = Column(String, nullable=False)  # EMAIL, LINKEDIN, CONTACT_FORM
    date = Column(Date, nullable=False, index=True)
    
    # Delivery metrics
    sent_count = Column(Integer, default=0)
    delivery_rate = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    
    # Engagement metrics
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    replied_count = Column(Integer, default=0)
    
    # Channel-specific rates
    reply_rate = Column(Float, default=0.0)
    click_through_rate = Column(Float, default=0.0)
    
    # Efficiency scoring
    cost_per_send = Column(Float, nullable=True)
    cost_per_engagement = Column(Float, nullable=True)
    efficiency_score = Column(Float, default=0.0)  # 0-100
    
    # Time tracking
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_channel_metrics_campaign_channel', 'campaign_id', 'channel'),
        Index('idx_channel_metrics_date', 'campaign_id', 'date'),
    )


class LeadAttributionDB(Base):
    """Multi-touch attribution tracking for each lead across channels."""
    __tablename__ = 'lead_attribution'
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('cam_leads.id'), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=False, index=True)
    
    # Attribution model configuration
    attribution_model = Column(String, nullable=False)  # FIRST_TOUCH, LAST_TOUCH, etc.
    
    # First and last touch channels
    first_touch_channel = Column(String, nullable=True)
    first_touch_date = Column(DateTime(timezone=True), nullable=True)
    last_touch_channel = Column(String, nullable=True)
    last_touch_date = Column(DateTime(timezone=True), nullable=True)
    
    # Attribution weights (JSON: {channel: weight})
    attribution_weights = Column(JSON, default={})
    
    # Touch sequence (JSON: list of {channel, timestamp, action})
    touch_sequence = Column(JSON, default=[])
    
    # Conversion attribution
    credit_allocated = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_attribution_lead_campaign', 'lead_id', 'campaign_id'),
        Index('idx_attribution_model', 'attribution_model'),
    )


class ABTestConfigDB(Base):
    """A/B test configuration and experiment setup."""
    __tablename__ = 'ab_test_config'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=False, index=True)
    
    # Test identification
    test_name = Column(String, nullable=False, unique=True)
    test_type = Column(String, nullable=False)  # MESSAGE, CHANNEL, TIMING, etc.
    status = Column(String, default='DRAFT')  # DRAFT, RUNNING, PAUSED, COMPLETED
    
    # Hypothesis and setup
    hypothesis = Column(String, nullable=False)
    control_variant = Column(String, nullable=False)
    treatment_variant = Column(String, nullable=False)
    
    # Sample configuration
    total_sample_size = Column(Integer, nullable=False)
    sample_split = Column(Float, default=0.5)  # 50/50 split
    
    # Statistical configuration
    confidence_level = Column(Float, default=0.95)  # 95%
    minimum_sample_per_variant = Column(Integer, default=50)
    
    # Scheduling
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(String, nullable=True)
    
    __table_args__ = (
        Index('idx_ab_test_campaign', 'campaign_id'),
        Index('idx_ab_test_status', 'status'),
    )


class ABTestResultDB(Base):
    """Results and statistical analysis of A/B test experiments."""
    __tablename__ = 'ab_test_result'
    
    id = Column(Integer, primary_key=True)
    test_config_id = Column(Integer, ForeignKey('ab_test_config.id'), nullable=False, index=True)
    
    # Sample data
    control_sample_size = Column(Integer, default=0)
    treatment_sample_size = Column(Integer, default=0)
    
    # Control group metrics
    control_metric_value = Column(Float, nullable=True)
    control_std_dev = Column(Float, nullable=True)
    
    # Treatment group metrics
    treatment_metric_value = Column(Float, nullable=True)
    treatment_std_dev = Column(Float, nullable=True)
    
    # Statistical results
    p_value = Column(Float, nullable=True)
    statistical_significance = Column(Boolean, default=False)
    confidence_interval = Column(JSON, default={})  # {lower: x, upper: y}
    effect_size = Column(Float, nullable=True)
    
    # Conclusion
    winner = Column(String, nullable=True)  # CONTROL, TREATMENT, INCONCLUSIVE
    recommendation = Column(String, nullable=True)
    
    # Computation metadata
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_ab_test_result_config', 'test_config_id'),
    )


class ROITrackerDB(Base):
    """Cost and revenue tracking for ROI calculations."""
    __tablename__ = 'roi_tracker'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey('cam_leads.id'), nullable=True, index=True)
    
    # Cost tracking
    acquisition_cost = Column(Float, nullable=False)
    channel = Column(String, nullable=True)  # Which channel contributed
    spend_date = Column(DateTime(timezone=True), nullable=False)
    
    # Revenue tracking (when available)
    deal_value = Column(Float, nullable=True)
    deal_date = Column(DateTime(timezone=True), nullable=True)
    deal_closed = Column(Boolean, default=False)
    
    # ROI calculation
    roi_percent = Column(Float, nullable=True)
    payback_period_days = Column(Integer, nullable=True)
    
    # Status
    reconciliation_status = Column(String, default='PENDING')  # PENDING, VERIFIED, RECONCILED
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_roi_tracker_campaign', 'campaign_id'),
        Index('idx_roi_tracker_lead', 'lead_id'),
        Index('idx_roi_tracker_spend_date', 'spend_date'),
    )


class CronExecutionDB(Base):
    """
    PHASE B HARDENING: Execution tracking for idempotent cron jobs.
    
    Prevents duplicate job executions even if cron schedules the same job twice.
    Tracks execution identity (deterministic), lock state, and outcomes.
    """
    __tablename__ = 'cam_cron_executions'
    
    id = Column(Integer, primary_key=True)
    
    # Deterministic execution identity
    # Format: "{job_type}_{campaign_id}_{scheduled_time_iso}"
    execution_id = Column(String, nullable=False, unique=True, index=True)
    
    # Job context
    job_type = Column(String, nullable=False, index=True)  # harvest, score, qualify, route, nurture, full_pipeline
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True, index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Execution tracking
    status = Column(String, nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, SKIPPED
    outcome = Column(String, nullable=True)  # SUCCESS, FAILURE, TIMEOUT, DUPLICATE_SKIPPED
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results
    leads_processed = Column(Integer, nullable=False, default=0)
    leads_succeeded = Column(Integer, nullable=False, default=0)
    leads_failed = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_cron_execution_job_type', 'job_type'),
        Index('idx_cron_execution_campaign', 'campaign_id'),
        Index('idx_cron_execution_scheduled', 'scheduled_time'),
        Index('idx_cron_execution_status', 'status'),
    )


class OutboundEmailDB(Base):
    """
    Outbound email database model (Phase 1).
    
    Tracks all emails sent via external providers (Resend, SMTP, etc.).
    Enables idempotency, reply threading, engagement tracking, and retry logic.
    """
    
    __tablename__ = "cam_outbound_emails"
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False, index=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False, index=True)
    
    # Email identity
    to_email = Column(String, nullable=False)
    from_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    
    # Content hash for idempotency (prevents duplicate sends of exact same content)
    content_hash = Column(String, nullable=True)
    
    # Provider information
    provider = Column(String, nullable=False)  # "Resend", "SMTP", "NoOp", etc.
    provider_message_id = Column(String, nullable=True, unique=True)  # ID from provider
    
    # Message-ID header for email threading
    message_id_header = Column(String, nullable=True, unique=True)
    
    # Email sequence tracking
    sequence_number = Column(Integer, nullable=True)  # Step in the sequence
    campaign_sequence_id = Column(String, nullable=True)  # Campaign-level sequence ID
    
    # Status and error tracking
    status = Column(String, nullable=False, default="QUEUED")  # QUEUED, SENT, FAILED, BOUNCED
    error_message = Column(Text, nullable=True)
    
    # Retry tracking
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    queued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    bounced_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata (renamed to email_metadata to avoid SQLAlchemy conflict)
    email_metadata = Column(JSON, nullable=True, default={})  # Tags, campaign info, etc.
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_outbound_email_lead', 'lead_id'),
        Index('idx_outbound_email_campaign', 'campaign_id'),
        Index('idx_outbound_email_status', 'status'),
        Index('idx_outbound_email_provider_msg_id', 'provider_message_id'),
        Index('idx_outbound_email_sent_at', 'sent_at'),
    )


class InboundEmailDB(Base):
    """
    Inbound email database model (Phase 2).
    
    Tracks emails received from leads (replies to outreach).
    Enables reply detection, classification, and reply-to-lead mapping.
    """
    
    __tablename__ = "cam_inbound_emails"
    
    id = Column(Integer, primary_key=True)
    
    # Foreign key (may be NULL if lead not yet identified)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True, index=True)
    
    # Idempotency: provider + message UID uniquely identifies an email
    # (prevents duplicate ingestion from IMAP polling)
    provider = Column(String, nullable=False)  # "IMAP", "Webhook", etc.
    provider_msg_uid = Column(String, nullable=False)  # IMAP UID, webhook ID, etc.
    
    # Email identity
    from_email = Column(String, nullable=False, index=True)
    to_email = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    
    # Email threading (original outbound message this replies to)
    in_reply_to_message_id = Column(String, nullable=True)  # In-Reply-To header value
    in_reply_to_outbound_email_id = Column(Integer, ForeignKey("cam_outbound_emails.id"), nullable=True)
    
    # Email content
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    
    # Classification (Phase 2)
    classification = Column(String, nullable=True)  # "POSITIVE", "NEGATIVE", "OOO", "BOUNCE", "UNSUB", "NEUTRAL"
    classification_confidence = Column(Float, nullable=True, default=0.0)  # 0.0-1.0
    classification_reason = Column(Text, nullable=True)
    
    # Temporal
    received_at = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Metadata (renamed to email_metadata to avoid SQLAlchemy conflict)
    email_metadata = Column(JSON, nullable=True, default={})  # Provider-specific data
    
    # Alert tracking (Phase 1: Worker)
    alert_sent = Column(Boolean, nullable=False, default=False)  # Has alert been sent for this reply?
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_inbound_email_lead', 'lead_id'),
        Index('idx_inbound_email_campaign', 'campaign_id'),
        Index('idx_inbound_email_from', 'from_email'),
        Index('idx_inbound_email_classification', 'classification'),
        Index('idx_inbound_email_received_at', 'received_at'),
        Index('idx_inbound_email_provider_uid', 'provider', 'provider_msg_uid'),  # Composite for idempotency
    )


class AnalyticsEventDB(Base):
    """Raw analytics events for granular tracking and debugging."""
    __tablename__ = 'analytics_event'
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey('cam_leads.id'), nullable=False, index=True)
    
    # Event classification
    event_type = Column(String, nullable=False)  # SENT, OPENED, CLICKED, REPLIED, etc.
    channel = Column(String, nullable=True)  # EMAIL, LINKEDIN, CONTACT_FORM
    
    # Event details (flexible JSON structure)
    event_data = Column(JSON, default={})  # Varies by event_type
    
    # Event timing
    event_timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Optional metadata
    outreach_attempt_id = Column(Integer, ForeignKey('cam_outreach_attempts.id'), nullable=True)
    
    __table_args__ = (
        Index('idx_analytics_event_campaign', 'campaign_id'),
        Index('idx_analytics_event_lead', 'lead_id'),
        Index('idx_analytics_event_type', 'event_type'),
        Index('idx_analytics_event_timestamp', 'event_timestamp'),
    )


class CamWorkerHeartbeatDB(Base):
    """
    Worker heartbeat for monitoring and single-worker locking.
    
    Used to:
    1. Track worker health (detect stuck/dead workers)
    2. Enforce single-worker constraint (advisory lock)
    """
    
    __tablename__ = "cam_worker_heartbeats"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, default='RUNNING')  # RUNNING, STOPPED, DEAD
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        Index('idx_worker_heartbeat_status', 'status'),
        Index('idx_worker_heartbeat_last_seen', 'last_seen_at'),
    )


class HumanAlertLogDB(Base):
    """
    Log of alerts sent to humans.
    
    Used for:
    1. Idempotency (prevent duplicate alerts)
    2. Audit trail (what was alerted and when)
    3. Alert delivery verification
    """
    
    __tablename__ = "cam_human_alert_logs"
    
    id = Column(Integer, primary_key=True)
    
    # Alert context
    alert_type = Column(String, nullable=False)  # POSITIVE_REPLY, CAMPAIGN_PAUSE, etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Associated entity (for idempotency)
    lead_id = Column(Integer, ForeignKey('cam_leads.id'), nullable=True)
    campaign_id = Column(Integer, ForeignKey('cam_campaigns.id'), nullable=True)
    inbound_email_id = Column(Integer, nullable=True)  # Reference to InboundEmailDB
    
    # Alert delivery
    recipients = Column(JSON, nullable=False, default=[])  # List of email addresses
    sent_successfully = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    
    # Idempotency
    idempotency_key = Column(String, nullable=True, unique=True)  # lead_id + event_type
    
    sent_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_alert_log_lead', 'lead_id'),
        Index('idx_alert_log_campaign', 'campaign_id'),
        Index('idx_alert_log_type', 'alert_type'),
        Index('idx_alert_log_sent_at', 'sent_at'),
        Index('idx_alert_log_idempotency', 'idempotency_key'),
    )


