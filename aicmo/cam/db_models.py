"""
CAM database models (SQLAlchemy).

Phase CAM-1: Persistent storage for campaigns, leads, and outreach attempts.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.sql import func

from aicmo.core.db import Base
from aicmo.cam.domain import LeadSource, LeadStatus, Channel, AttemptStatus


class CampaignDB(Base):
    """
    Outreach campaign database model.
    
    Groups leads together for coordinated messaging and tracking.
    """
    
    __tablename__ = "cam_campaigns"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    target_niche = Column(String, nullable=True)
    active = Column(Boolean, nullable=False, default=True)

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
