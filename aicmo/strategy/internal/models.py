"""
Strategy module database models.

Contains persistent storage for strategy-owned data:
- StrategyDocumentDB: Strategy documents with KPIs, channels, and timelines

Phase 4 Lane B: Real database persistence for strategy entities.

Idempotency Key: (brief_id, version)
- A brief can have multiple strategy versions
- Same version number for same brief is idempotent (enforced by unique constraint)
- No workflow_run_id exists in ports, so we use (brief_id, version) as stable key
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, JSON, UniqueConstraint

from aicmo.core.db import Base


class StrategyDocumentDB(Base):
    """
    Persistent storage for strategy documents.
    
    Strategy documents define campaign approach, KPIs, channels, and timeline.
    Used by downstream modules (Production, QC, Delivery).
    
    Idempotency: Enforced via unique constraint on (brief_id, version).
    Multiple versions per brief are allowed, but same (brief_id, version) 
    combination will fail on duplicate insert.
    """
    
    __tablename__ = "strategy_document"
    
    # Primary key
    id = Column(String, primary_key=True)  # strategy_id (UUID as string)
    
    # Parent reference (no FK - decoupled from onboarding module)
    brief_id = Column(String, nullable=False)  # Logical reference only
    
    # Version tracking
    version = Column(Integer, nullable=False)  # Version number (1, 2, 3, ...)
    
    # Strategy content (JSON serialized complex objects)
    kpis = Column(JSON, nullable=False, default=list)  # List[KpiDTO] serialized
    channels = Column(JSON, nullable=False, default=list)  # List[ChannelPlanDTO] serialized
    timeline = Column(JSON, nullable=False, default=dict)  # TimelineDTO serialized
    executive_summary = Column(Text, nullable=False)
    
    # Approval tracking
    is_approved = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps (application-controlled, not DB defaults)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    
    # Idempotency constraint: (brief_id, version) must be unique
    __table_args__ = (
        UniqueConstraint('brief_id', 'version', name='uq_strategy_brief_version'),
    )
