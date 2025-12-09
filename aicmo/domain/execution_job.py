"""Execution job domain models with database persistence mapping.

Stage 3: ExecutionJob wraps ExecutionJobDB for tracking content delivery
jobs through the execution pipeline.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from .base import AicmoBaseModel
from .execution import ContentItem


class ExecutionJob(AicmoBaseModel):
    """
    Domain model for an execution job.
    
    Stage 3: Tracks content delivery jobs from QUEUED → DONE
    with retry logic and external ID tracking.
    """
    
    id: Optional[int] = None
    campaign_id: int
    creative_id: Optional[int] = None
    
    # Job details
    job_type: str  # "social_post", "email", "crm_sync"
    platform: str  # "instagram", "linkedin", "twitter", "email"
    payload: Dict[str, Any]  # ContentItem dict or job-specific data
    
    # Execution tracking
    status: str = "QUEUED"  # QUEUED, IN_PROGRESS, DONE, FAILED
    retries: int = 0
    max_retries: int = 3
    
    # Results
    external_id: Optional[str] = None
    last_error: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_content_item(
        cls,
        content: ContentItem,
        campaign_id: int,
        creative_id: Optional[int] = None
    ) -> "ExecutionJob":
        """
        Create ExecutionJob from ContentItem.
        
        Args:
            content: Content to be published
            campaign_id: Campaign ID
            creative_id: Optional creative asset ID
            
        Returns:
            ExecutionJob ready for persistence
        """
        return cls(
            campaign_id=campaign_id,
            creative_id=creative_id,
            job_type="social_post",
            platform=content.platform,
            payload=content.model_dump(),
            status="QUEUED"
        )
    
    @classmethod
    def from_db(cls, db_job) -> "ExecutionJob":
        """
        Create ExecutionJob from ExecutionJobDB.
        
        Args:
            db_job: ExecutionJobDB instance
            
        Returns:
            ExecutionJob domain model
        """
        return cls(
            id=db_job.id,
            campaign_id=db_job.campaign_id,
            creative_id=db_job.creative_id,
            job_type=db_job.job_type,
            platform=db_job.platform,
            payload=db_job.payload,
            status=db_job.status,
            retries=db_job.retries,
            max_retries=db_job.max_retries,
            external_id=db_job.external_id,
            last_error=db_job.last_error,
            completed_at=db_job.completed_at
        )
    
    def apply_to_db(self, db_job) -> None:
        """
        Apply ExecutionJob state to ExecutionJobDB instance.
        
        Args:
            db_job: ExecutionJobDB instance to update
        """
        db_job.campaign_id = self.campaign_id
        db_job.creative_id = self.creative_id
        db_job.job_type = self.job_type
        db_job.platform = self.platform
        db_job.payload = self.payload
        db_job.status = self.status
        db_job.retries = self.retries
        db_job.max_retries = self.max_retries
        db_job.external_id = self.external_id
        db_job.last_error = self.last_error
        db_job.completed_at = self.completed_at
    
    def to_content_item(self) -> ContentItem:
        """
        Convert ExecutionJob payload back to ContentItem.
        
        Returns:
            ContentItem for execution
        """
        return ContentItem(**self.payload)
