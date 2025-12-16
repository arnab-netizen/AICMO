"""
Venture and Campaign Configuration Models.

MODULE 0: Foundation for multi-venture marketing engine.
Enables multiple businesses/products/offers to be managed independently.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from aicmo.core.db import Base


class CampaignStatus(enum.Enum):
    """Campaign lifecycle status."""
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"


class VentureDB(Base):
    """
    Venture: A business, product, or offer being marketed.
    
    Enables multi-tenant marketing where one AICMO instance manages
    campaigns for multiple ventures (SaaS products, consulting services,
    events, political campaigns, NGO programs, creator content, etc.).
    """
    __tablename__ = "ventures"
    
    id = Column(String, primary_key=True)  # e.g., "acme-saas", "consulting-2024"
    venture_name = Column(String, nullable=False)
    offer_summary = Column(Text, nullable=False)  # What are we selling/promoting?
    primary_cta = Column(String, nullable=False)  # "Book a demo", "Sign up", "Donate"
    
    # Default configuration
    default_channels = Column(JSON, nullable=False, default=["email"])  # email, linkedin, contact_form
    timezone = Column(String, nullable=False, default="UTC")
    owner_contact = Column(String, nullable=False)  # Who owns this venture
    
    # Metadata
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class CampaignConfigDB(Base):
    """
    Campaign Configuration: Execution parameters for a marketing campaign.
    
    Defines HOW a campaign runs: channels, limits, safety controls.
    Multiple campaigns can belong to one venture.
    """
    __tablename__ = "campaign_configs"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False, unique=True)
    venture_id = Column(String, ForeignKey("ventures.id"), nullable=False)
    
    # Objectives
    objective = Column(Text, nullable=False)  # What is this campaign trying to achieve?
    
    # Channel controls
    allowed_channels = Column(JSON, nullable=False, default=["email"])
    daily_send_limit = Column(Integer, nullable=False, default=50)
    
    # Safety controls (CRITICAL)
    status = Column(SAEnum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    kill_switch = Column(Boolean, nullable=False, default=False)  # Emergency stop
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
