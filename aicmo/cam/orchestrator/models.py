"""
Orchestrator database models.

Provides:
- Single-writer lease (orchestrator_runs)
- Unsubscribe list (cam_unsubscribes)
- Suppression list (cam_suppressions)
"""

import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func

from aicmo.core.db import Base


class RunStatus(enum.Enum):
    """Orchestrator run status."""
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class OrchestratorRunDB(Base):
    """
    Orchestrator run state with single-writer lease.
    
    Ensures only one orchestrator instance processes a campaign at a time.
    Uses atomic UPDATE for lease acquisition.
    """
    __tablename__ = "cam_orchestrator_runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(Integer, nullable=False, index=True)
    
    status = Column(String, nullable=False, default=RunStatus.CLAIMED.value)
    claimed_by = Column(String, nullable=False)  # worker_id
    
    # Lease management
    lease_expires_at = Column(DateTime(timezone=True), nullable=False)
    heartbeat_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Progress tracking
    leads_processed = Column(Integer, nullable=False, default=0)
    jobs_created = Column(Integer, nullable=False, default=0)
    attempts_succeeded = Column(Integer, nullable=False, default=0)
    attempts_failed = Column(Integer, nullable=False, default=0)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_orchestrator_campaign_status', 'campaign_id', 'status'),
        Index('idx_orchestrator_lease', 'campaign_id', 'lease_expires_at'),
    )


class UnsubscribeDB(Base):
    """
    Unsubscribe list.
    
    Hard block: If email is in this table, never contact via any channel.
    """
    __tablename__ = "cam_unsubscribes"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True, index=True)
    
    reason = Column(String, nullable=True)  # "user_request", "bounce_hard", "spam_complaint"
    campaign_id = Column(Integer, nullable=True)  # Which campaign triggered unsubscribe
    
    unsubscribed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SuppressionDB(Base):
    """
    Suppression list.
    
    Broader than unsubscribe - can block by email, domain, or identity_hash.
    """
    __tablename__ = "cam_suppressions"
    
    id = Column(Integer, primary_key=True)
    
    # Block criteria (at least one must be set)
    email = Column(String, nullable=True, index=True)
    domain = Column(String, nullable=True, index=True)
    identity_hash = Column(String, nullable=True, index=True)
    
    reason = Column(String, nullable=False)  # "dnc_list", "competitor", "legal_hold"
    active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_suppression_email', 'email', 'active'),
        Index('idx_suppression_domain', 'domain', 'active'),
        Index('idx_suppression_hash', 'identity_hash', 'active'),
    )
