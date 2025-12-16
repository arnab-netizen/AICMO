"""
Distribution Job database model.

MODULE 2: Tracks outreach execution with safety controls.
Phase 2 Orchestrator: Extended with idempotency and retry scheduling.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func

from aicmo.core.db import Base


class DistributionJobDB(Base):
    """
    Distribution Job: A single outreach attempt to a lead.
    
    Tracks every message sent, enabling:
    - Rate limiting
    - Unsubscribe enforcement
    - Attribution
    - Proof of execution
    - Idempotency (Phase 2)
    - Retry scheduling (Phase 2)
    """
    __tablename__ = "distribution_jobs"
    
    id = Column(Integer, primary_key=True)
    venture_id = Column(String, ForeignKey("ventures.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=False)
    
    channel = Column(String, nullable=False)  # email, linkedin, sms, etc.
    message_id = Column(String, nullable=True)  # External provider message ID
    
    status = Column(String, nullable=False)  # PENDING, SENT, FAILED, BLOCKED, RETRY_SCHEDULED, SENT_PROOF
    error = Column(Text, nullable=True)  # Error message if failed
    
    # Phase 2: Idempotency and retry
    idempotency_key = Column(String, nullable=True, unique=True, index=True)
    step_index = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_distribution_campaign', 'campaign_id'),
        Index('idx_distribution_status', 'status'),
        Index('idx_distribution_lead', 'lead_id'),
        Index('idx_distribution_idempotency', 'idempotency_key', unique=True),
    )
