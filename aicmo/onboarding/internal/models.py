"""
Onboarding module database models.

Contains persistent storage for onboarding-owned data:
- BriefDB: Normalized project briefs with scope and objectives
- IntakeDB: Raw intake form responses (pre-normalization)

Phase 4 Lane B: Real database persistence for onboarding entities.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON

from aicmo.core.db import Base


class BriefDB(Base):
    """
    Persistent storage for normalized project briefs.
    
    Briefs are the starting point of the ClientToDeliveryWorkflow.
    Contains validated, structured project requirements from client onboarding.
    """
    
    __tablename__ = "onboarding_brief"
    
    # Primary key
    id = Column(String, primary_key=True)  # brief_id (UUID as string)
    
    # Client reference (no FK - decoupled from potential future client module)
    client_id = Column(String, nullable=False)
    
    # Scope
    deliverables = Column(JSON, nullable=False, default=list)  # List[str]
    exclusions = Column(JSON, nullable=False, default=list)  # List[str]
    timeline_weeks = Column(String, nullable=True)  # "8", "12-16", etc.
    
    # Objectives and audience
    objectives = Column(JSON, nullable=False, default=list)  # List[str]
    target_audience = Column(Text, nullable=False)
    
    # Brand guidelines
    brand_guidelines = Column(JSON, nullable=False, default=dict)  # Dict[str, Any]
    
    # Additional metadata (use underscore + name parameter to avoid SQLAlchemy reserved word)
    meta_data = Column("metadata", JSON, nullable=False, default=dict)
    
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
    normalized_at = Column(DateTime(timezone=True), nullable=False)


class IntakeDB(Base):
    """
    Persistent storage for raw intake form responses.
    
    Captures client submissions before normalization into structured Brief.
    Optional: Only needed if workflow requires intake history retrieval.
    """
    
    __tablename__ = "onboarding_intake"
    
    # Primary key
    id = Column(String, primary_key=True)  # intake_id (UUID as string)
    
    # Link to brief (if normalized)
    brief_id = Column(String, nullable=True)  # Populated after normalization
    
    # Client reference
    client_id = Column(String, nullable=False)
    
    # Raw form data
    responses = Column(JSON, nullable=False, default=dict)  # Dict[str, Any]
    
    # Attachments (URLs or file references)
    attachments = Column(JSON, nullable=False, default=list)  # List[str]
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=False)
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
