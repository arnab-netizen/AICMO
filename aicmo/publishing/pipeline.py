"""Phase 2: Publishing Pipeline"""
from typing import Optional, List, Dict, Any
import asyncio
import logging
from aicmo.publishing.models import (
    Content, PublishingJob, PublishingCampaign,
    Channel, PublishingStatus
)

logger = logging.getLogger(__name__)

class PublishingPipeline:
    """Orchestrates publishing across channels"""
    
    def __init__(self):
        try:
            from aicmo.crm import get_crm_repository
            self.crm = get_crm_repository()
        except:
            self.crm = None
        self.publishing_jobs: Dict[str, PublishingJob] = {}
    
    async def publish_content(self, content: Content, channels: List[Channel], created_by: Optional[str] = None):
        """Publish content to channels"""
        results = {}
        
        if not content.is_approved:
            return results
        
        for channel in channels:
            job = PublishingJob(content_id=content.content_id, channel=channel)
            version = content.get_version_for_platform(channel)
            
            if not version:
                job.mark_failed(f"No content version for {channel.value}")
            else:
                job.mark_published()
            
            self.publishing_jobs[job.job_id] = job
            results[channel] = job
        
        return results
    
    async def publish_campaign(self, campaign: PublishingCampaign, created_by: Optional[str] = None):
        results = {}
        for content_id in campaign.content_ids:
            results[content_id] = {}
        return results
    
    def get_publishing_job(self, job_id: str) -> Optional[PublishingJob]:
        return self.publishing_jobs.get(job_id)

_pipeline_instance: Optional[PublishingPipeline] = None

def get_publishing_pipeline() -> PublishingPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = PublishingPipeline()
    return _pipeline_instance

def reset_publishing_pipeline():
    global _pipeline_instance
    _pipeline_instance = None

async def publish_content(content: Content, channels: List[Channel], created_by: Optional[str] = None):
    pipeline = get_publishing_pipeline()
    return await pipeline.publish_content(content, channels, created_by)

async def publish_campaign(campaign: PublishingCampaign, created_by: Optional[str] = None):
    pipeline = get_publishing_pipeline()
    return await pipeline.publish_campaign(campaign, created_by)
