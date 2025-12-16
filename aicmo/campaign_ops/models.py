"""
Campaign Operations SQLAlchemy Models

Tables:
- campaign_ops_campaigns: Campaign metadata
- campaign_ops_plans: Generated strategy/angles
- campaign_ops_calendar_items: Scheduled posts per platform
- campaign_ops_operator_tasks: Operator action items (posts, engagement, follow-ups)
- campaign_ops_metric_entries: Manual metric logging
- campaign_ops_audit_log: Accountability log
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CampaignStatus(str, Enum):
    """Campaign lifecycle states."""
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class TaskStatus(str, Enum):
    """Task execution states."""
    PENDING = "PENDING"
    DUE = "DUE"
    OVERDUE = "OVERDUE"
    DONE = "DONE"
    MISSED = "MISSED"
    BLOCKED = "BLOCKED"


class TaskType(str, Enum):
    """Operator task types."""
    POST = "POST"
    ENGAGE = "ENGAGE"
    FOLLOW_UP = "FOLLOW_UP"
    REVIEW = "REVIEW"
    ANALYZE = "ANALYZE"
    MANUAL = "MANUAL"


class ContentType(str, Enum):
    """Content format types."""
    POST = "post"
    CAROUSEL = "carousel"
    REEL = "reel"
    THREAD = "thread"
    STORY = "story"
    EMAIL = "email"
    DM = "dm"
    OTHER = "other"


class CompletionProofType(str, Enum):
    """Proof of completion types."""
    URL = "URL"
    TEXT = "TEXT"
    UPLOAD = "UPLOAD"
    MANUAL = "MANUAL"


class Campaign(Base):
    """Campaign metadata and configuration."""
    __tablename__ = "campaign_ops_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    client_name = Column(String(255), nullable=False)
    venture_name = Column(String(255), nullable=True)
    objective = Column(Text, nullable=False)
    platforms = Column(JSON, nullable=False, default=list)  # ["linkedin", "instagram", "twitter"]
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    cadence = Column(JSON, nullable=False, default=dict)  # {"linkedin": 3, "instagram": 5, "twitter": 2}
    primary_cta = Column(String(255), nullable=False)
    lead_capture_method = Column(String(255), nullable=True)  # "dm", "form", "email", etc.
    status = Column(String(20), nullable=False, default=CampaignStatus.PLANNED.value, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plans = relationship("CampaignPlan", back_populates="campaign", cascade="all, delete-orphan")
    calendar_items = relationship("CalendarItem", back_populates="campaign", cascade="all, delete-orphan")
    tasks = relationship("OperatorTask", back_populates="campaign", cascade="all, delete-orphan")
    metric_entries = relationship("MetricEntry", back_populates="campaign", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_campaign_ops_campaigns_status_created", "status", "created_at"),
    )


class CampaignPlan(Base):
    """Generated campaign strategy and angles."""
    __tablename__ = "campaign_ops_plans"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaign_ops_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Plan content
    angles_json = Column(JSON, nullable=True)  # List of angles/hooks
    positioning_json = Column(JSON, nullable=True)  # Positioning statement
    messaging_json = Column(JSON, nullable=True)  # Key messages by theme
    weekly_themes_json = Column(JSON, nullable=True)  # Weekly themes/focus
    
    generated_by = Column(String(50), nullable=False, default="manual")  # "manual" or "aicmo"
    version = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    campaign = relationship("Campaign", back_populates="plans")

    __table_args__ = (
        Index("ix_campaign_ops_plans_campaign_version", "campaign_id", "version"),
    )


class CalendarItem(Base):
    """Scheduled post in campaign calendar."""
    __tablename__ = "campaign_ops_calendar_items"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaign_ops_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    platform = Column(String(50), nullable=False)  # "linkedin", "instagram", "twitter"
    content_type = Column(String(50), nullable=False, default=ContentType.POST.value)  # "post", "carousel", "reel"
    scheduled_at = Column(DateTime, nullable=False, index=True)
    
    title = Column(String(255), nullable=True)  # Short name for reference
    copy_text = Column(Text, nullable=True)  # Post copy/caption
    asset_ref = Column(String(512), nullable=True)  # Path to image/video or description
    cta_text = Column(String(255), nullable=True)  # Call-to-action text
    
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    campaign = relationship("Campaign", back_populates="calendar_items")

    __table_args__ = (
        Index("ix_campaign_ops_calendar_items_campaign_scheduled", "campaign_id", "scheduled_at"),
        Index("ix_campaign_ops_calendar_items_platform_status", "platform", "status"),
    )


class OperatorTask(Base):
    """Task assigned to operator for manual execution."""
    __tablename__ = "campaign_ops_operator_tasks"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaign_ops_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    calendar_item_id = Column(Integer, ForeignKey("campaign_ops_calendar_items.id", ondelete="SET NULL"), nullable=True)
    
    task_type = Column(String(50), nullable=False, default=TaskType.POST.value)  # "POST", "ENGAGE", "FOLLOW_UP", etc.
    platform = Column(String(50), nullable=False)  # "linkedin", "instagram", "twitter", "email"
    
    due_at = Column(DateTime, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    
    # Execution instructions
    instructions_text = Column(Text, nullable=False)  # WHERE + HOW to do this
    copy_text = Column(Text, nullable=True)  # Text to use (editable)
    asset_ref = Column(String(512), nullable=True)  # Asset location/description
    
    status = Column(String(20), nullable=False, default=TaskStatus.PENDING.value, index=True)
    
    # Completion tracking
    completion_proof_type = Column(String(50), nullable=True)  # "URL", "TEXT", "UPLOAD"
    completion_proof_value = Column(Text, nullable=True)  # URL, text content, or file reference
    completed_at = Column(DateTime, nullable=True)
    
    blocked_reason = Column(Text, nullable=True)  # If blocked, why
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="tasks")

    __table_args__ = (
        Index("ix_campaign_ops_operator_tasks_campaign_due", "campaign_id", "due_at"),
        Index("ix_campaign_ops_operator_tasks_platform_status", "platform", "status"),
        Index("ix_campaign_ops_operator_tasks_status_due", "status", "due_at"),
    )


class MetricEntry(Base):
    """Manually logged performance metrics."""
    __tablename__ = "campaign_ops_metric_entries"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaign_ops_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    
    platform = Column(String(50), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    metric_name = Column(String(100), nullable=False)  # "impressions", "engagement", "clicks", etc.
    metric_value = Column(Float, nullable=False)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship
    campaign = relationship("Campaign", back_populates="metric_entries")

    __table_args__ = (
        Index("ix_campaign_ops_metric_entries_campaign_date", "campaign_id", "date"),
        Index("ix_campaign_ops_metric_entries_platform_metric", "platform", "metric_name"),
    )


class OperatorAuditLog(Base):
    """Audit log for accountability and reproducibility."""
    __tablename__ = "campaign_ops_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    
    actor = Column(String(100), nullable=False)  # "operator" or user name
    action = Column(String(255), nullable=False)  # "created_campaign", "completed_task", etc.
    
    entity_type = Column(String(50), nullable=True)  # "campaign", "task", "metric"
    entity_id = Column(Integer, nullable=True)
    
    # JSON snapshots for full traceability
    before_json = Column(JSON, nullable=True)
    after_json = Column(JSON, nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_campaign_ops_audit_log_actor_created", "actor", "created_at"),
        Index("ix_campaign_ops_audit_log_entity", "entity_type", "entity_id"),
    )
