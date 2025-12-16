"""
Delivery module database models.

Contains persistent storage for delivery-owned data:
- DeliveryJobDB: Execution jobs tracking content delivery through pipeline (legacy)
- DeliveryPackageDB: Phase 4 Lane B - Delivery packages
- DeliveryArtifactDB: Phase 4 Lane B - Package artifacts

Moved from cam.db_models during Phase 4 enforcement hardening.
Execution jobs belong to the Delivery domain, not CAM.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from aicmo.core.db import Base


class DeliveryJobDB(Base):
    """
    Persistent storage for execution jobs.
    
    Formerly: ExecutionJobDB in cam.db_models
    
    Stage 3: Tracks social posts and other content delivery jobs
    through the execution pipeline from QUEUED → DONE.
    
    Data Ownership: DELIVERY module owns execution/publishing pipeline.
    The campaign_id and creative_id are logical references (no FKs to preserve decoupling).
    """
    
    __tablename__ = "delivery_jobs"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, nullable=False)  # Logical reference, no FK
    creative_id = Column(Integer, nullable=True)  # Logical reference, no FK
    
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
    result_message = Column(String, nullable=True)  # Success/error message
    result_data = Column(JSON, nullable=True)  # Platform response data
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class DeliveryPackageDB(Base):
    """
    Database model for delivery packages (Phase 4 Lane B).
    
    Idempotency: package_id is unique (latest package wins on re-save).
    No cross-module foreign keys: draft_id stored as String.
    """
    __tablename__ = "delivery_packages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(String, nullable=False, unique=True)  # Business key (index in __table_args__)
    draft_id = Column(String, nullable=False)  # Logical reference (index in __table_args__)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to artifacts (explicit primaryjoin since no FK)
    artifacts = relationship(
        "DeliveryArtifactDB",
        primaryjoin="DeliveryPackageDB.package_id == foreign(DeliveryArtifactDB.package_id)",
        back_populates="package",
        cascade="all, delete-orphan",
        lazy="joined",  # Eager load for query efficiency
    )
    
    __table_args__ = (
        Index("ix_delivery_packages_package_id", "package_id"),
        Index("ix_delivery_packages_draft_id", "draft_id"),
    )


class DeliveryArtifactDB(Base):
    """
    Database model for delivery artifacts (Phase 4 Lane B).
    
    Child of DeliveryPackageDB with cascade delete.
    Position field ensures deterministic ordering.
    """
    __tablename__ = "delivery_artifacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(String, nullable=False)  # Parent reference (index in __table_args__)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    format = Column(String, nullable=False)
    position = Column(Integer, nullable=False)  # Ordering within package
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship to parent package (explicit primaryjoin since no FK)
    package = relationship(
        "DeliveryPackageDB",
        primaryjoin="foreign(DeliveryArtifactDB.package_id) == DeliveryPackageDB.package_id",
        back_populates="artifacts"
    )
    
    __table_args__ = (
        Index("ix_delivery_artifacts_package_id", "package_id"),
        Index("ix_delivery_artifacts_package_id_position", "package_id", "position"),
    )
