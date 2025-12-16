"""
Import batch tracking for lead ingestion auditing.

MODULE 1: Lead Capture + Attribution
Tracks CSV imports, API ingests, and bulk operations for compliance and debugging.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from aicmo.core.db import Base


class ImportBatchDB(Base):
    """
    Tracks batch imports of leads for auditing and attribution.
    
    Every CSV import, API bulk ingestion, or manual upload creates one ImportBatch.
    Links leads back to their source for compliance and debugging.
    """
    
    __tablename__ = "cam_import_batches"
    
    id = Column(Integer, primary_key=True)
    
    # Provenance tracking
    file_name = Column(String, nullable=True)  # Original filename if CSV
    file_hash = Column(String, nullable=True)  # SHA256 of uploaded file (dedup)
    uploaded_by = Column(String, nullable=False)  # operator@example.com or "api_key_xyz"
    
    # Source metadata
    source_system = Column(String, nullable=True)  # "apollo", "linkedin_export", "manual_entry"
    source_list_name = Column(String, nullable=True)  # "Q4_2025_SaaS_Founders", "Webinar_Attendees"
    
    # Import results
    total_rows = Column(Integer, nullable=False, default=0)
    successful_imports = Column(Integer, nullable=False, default=0)
    failed_imports = Column(Integer, nullable=False, default=0)
    duplicate_skips = Column(Integer, nullable=False, default=0)
    
    # Error tracking
    error_log = Column(Text, nullable=True)  # Newline-separated errors
    
    # Campaign association (optional - batch may span multiple campaigns)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True)
    venture_id = Column(String, ForeignKey("ventures.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
