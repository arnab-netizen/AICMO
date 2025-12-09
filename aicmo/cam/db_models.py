"""
CAM database models (SQLAlchemy).

Phase CAM-1: Persistent storage for campaigns, leads, and outreach attempts.
Phase CAM-7: Discovery jobs and discovered profiles for ethical lead finding.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    Enum as SAEnum,
    ForeignKey,
    JSON,
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
    
    # Phase 9: Human review queue
    requires_human_review = Column(Boolean, nullable=False, default=False)
    review_type = Column(String, nullable=True)  # e.g. "MESSAGE", "PROPOSAL", "PRICING"
    review_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class OutreachAttemptDB(Base):
    """
    Outreach attempt database model.
    
    Tracks execution status, errors, and timing for analytics and follow-up scheduling.
    """
    
    __tablename__ = "cam_outreach_attempts"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    channel = Column(SAEnum(Channel), nullable=False)
    step_number = Column(Integer, nullable=False)

    status = Column(SAEnum(AttemptStatus), nullable=False, default=AttemptStatus.PENDING)
    last_error = Column(Text, nullable=True)

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

