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
from aicmo.cam.domain import LeadSource, LeadStatus, Channel, AttemptStatus


class CampaignDB(Base):
    """
    Outreach campaign database model.
    
    Groups leads together for coordinated messaging and tracking.
    Phase 9.1: Added strategy document storage and status tracking.
    """
    
    __tablename__ = "cam_campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    target_niche = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    
    # Strategy document storage (Phase 9.1)
    strategy_text = Column(Text, nullable=True)
    strategy_status = Column(String, nullable=True, default="DRAFT")  # DRAFT, APPROVED, REJECTED
    strategy_rejection_reason = Column(Text, nullable=True)
    
    # Intake context (Phase 9.1)
    intake_goal = Column(Text, nullable=True)
    intake_constraints = Column(Text, nullable=True)
    intake_audience = Column(Text, nullable=True)
    intake_budget = Column(String, nullable=True)

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

    notes = Column(Text, nullable=True)

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

