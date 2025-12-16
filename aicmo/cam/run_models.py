"""
Campaign run tracking models.

Tracks every campaign execution for audit and recovery.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.sql import func

from aicmo.core.db import Base


class CampaignRunDB(Base):
    """
    Campaign Run: Tracks every execution of a campaign.
    
    Enables audit trail and crash recovery.
    Each time a campaign runs (manually or scheduled), a run is created.
    """
    __tablename__ = "campaign_runs"
    
    id = Column(String, primary_key=True)  # UUID
    campaign_id = Column(Integer, nullable=False, index=True)
    venture_id = Column(String, nullable=False, index=True)
    
    # Run metadata
    status = Column(String, nullable=False)  # RUNNING, COMPLETED, FAILED, CANCELLED
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Execution context
    mode = Column(String, nullable=False)  # proof, live
    batch_size = Column(Integer, nullable=True)
    triggered_by = Column(String, nullable=True)  # "operator", "scheduler", "api"
    
    # Results
    leads_processed = Column(Integer, nullable=False, default=0)
    jobs_created = Column(Integer, nullable=False, default=0)
    jobs_succeeded = Column(Integer, nullable=False, default=0)
    jobs_failed = Column(Integer, nullable=False, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_context = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    @staticmethod
    def generate_run_id() -> str:
        """Generate unique run ID."""
        return str(uuid.uuid4())
