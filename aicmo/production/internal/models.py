"""
Production module database models.

Contains persistent storage for production-owned data:
- ProductionAssetDB: Generated creative assets with publishing metadata (legacy Stage 2)
- ContentDraftDB: Content drafts generated from strategy (ports-aligned)
- DraftBundleDB: Assembly coordination for draft + assets (ports-aligned)
- BundleAssetDB: Creative assets within bundles (ports-aligned)

Phase 4 Lane B: Added ContentDraftDB, DraftBundleDB, BundleAssetDB for ports persistence.
Legacy ProductionAssetDB kept for backward compatibility (not used by current ports).
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from aicmo.core.db import Base


class ProductionAssetDB(Base):
    """
    Persistent storage for generated creative assets.
    
    Formerly: CreativeAssetDB in cam.db_models
    
    Stage 2: Links CreativeVariants to campaigns with publish status tracking.
    Enables asset library management and execution pipeline integration.
    
    Data Ownership: PRODUCTION module owns creative content generation.
    The campaign_id is a logical reference (no FK to preserve decoupling).
    
    **NOTE**: This is LEGACY model for Stage 2 creative publishing workflow.
    Current ports (generate_draft, assemble_bundle) use ContentDraftDB/DraftBundleDB instead.
    """
    
    __tablename__ = "production_assets"
    
    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, nullable=False)  # Logical reference, no FK
    
    # Creative content
    platform = Column(String, nullable=False)  # "instagram", "linkedin", "twitter"
    format = Column(String, nullable=False)  # "reel", "post", "carousel", "thread"
    hook = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    cta = Column(String, nullable=True)
    tone = Column(String, nullable=True)  # "professional", "friendly", "bold"
    
    # Publishing tracking
    publish_status = Column(String, nullable=False, default="DRAFT")  # DRAFT, APPROVED, SCHEDULED, PUBLISHED
    scheduled_date = Column(String, nullable=True)  # ISO date string
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    meta = Column(JSON, nullable=True)  # Additional creative metadata
    
    # Audit timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ContentDraftDB(Base):
    """
    Persistent storage for content drafts generated from strategy.
    
    Supports port: DraftGeneratePort.generate_draft(strategy_id) → ContentDraftDTO
    
    Idempotency Key: draft_id (unique constraint ensures no duplicates)
    Compensation: DELETE (drafts can be regenerated without state accumulation)
    """
    
    __tablename__ = "production_drafts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    draft_id = Column(String, nullable=False, unique=True)  # Idempotency key
    strategy_id = Column(String, nullable=False, index=True)  # Logical FK (no ForeignKey)
    content_type = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class DraftBundleDB(Base):
    """
    Persistent storage for draft bundles (assembly coordination).
    
    Supports port: AssetAssemblePort.assemble_bundle(draft_id) → DraftBundleDTO
    
    Idempotency Key: bundle_id (unique constraint ensures no duplicates)
    Compensation: DELETE (bundles can be reassembled without state accumulation)
    """
    
    __tablename__ = "production_bundles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bundle_id = Column(String, nullable=False, unique=True)  # Idempotency key
    draft_id = Column(String, nullable=False, index=True)  # Logical FK to ContentDraft (no ForeignKey)
    assembled_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class BundleAssetDB(Base):
    """
    Persistent storage for creative assets within draft bundles.
    
    Many-to-one relationship: multiple assets per bundle (no SQLAlchemy relationship()).
    
    Supports: AssetDTO entities within DraftBundleDTO.assets list
    
    Idempotency Key: asset_id (unique constraint ensures no duplicates)
    Compensation: DELETE (assets regenerated with bundle)
    """
    
    __tablename__ = "production_bundle_assets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String, nullable=False, unique=True)  # Idempotency key
    bundle_id = Column(String, nullable=False, index=True)  # Logical FK to Bundle (no ForeignKey)
    asset_type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    meta = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
