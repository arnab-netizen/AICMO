"""
Integration Tests for Phase 2: Publishing & Ads Execution

Tests:
1. Content Model Tests
2. Publishing Job Tests  
3. Publishing Campaign Tests
4. Publishing Pipeline Tests
5. Multi-Channel Publishing Tests

Run with: pytest tests/test_phase2_publishing.py -v
"""

import pytest
from datetime import datetime
from aicmo.publishing import (
    ContentType, Channel, PublishingStatus, PublishingMetrics,
    ContentVersion, Content, PublishingJob, PublishingCampaign,
    get_publishing_pipeline, reset_publishing_pipeline,
)


class TestContentModel:
    """Test Content data model."""
    
    def test_content_creation(self):
        """Test creating content."""
        content = Content(
            content_type=ContentType.SOCIAL_POST,
            title="Test Post",
            primary_content="This is a test post"
        )
        assert content.content_type == ContentType.SOCIAL_POST
        assert content.title == "Test Post"
        assert content.is_draft == True
        assert content.is_approved == False
    
    def test_add_platform_version(self):
        """Test adding platform-specific versions."""
        content = Content(title="Test")
        
        linkedin_version = ContentVersion(
            platform=Channel.LINKEDIN,
            title="LinkedIn Title",
            body="LinkedIn content"
        )
        content.add_version(linkedin_version)
        
        assert len(content.platform_versions) == 1
        assert content.get_version_for_platform(Channel.LINKEDIN) is not None
    
    def test_approve_content(self):
        """Test approving content."""
        content = Content(title="Test")
        assert content.is_draft == True
        assert content.is_approved == False
        
        content.approve("Looks good")
        
        assert content.is_draft == False
        assert content.is_approved == True
        assert content.approval_notes == "Looks good"


class TestPublishingJob:
    """Test PublishingJob model."""
    
    def test_job_creation(self):
        """Test creating publishing job."""
        job = PublishingJob(
            content_id="content-123",
            channel=Channel.LINKEDIN
        )
        assert job.content_id == "content-123"
        assert job.channel == Channel.LINKEDIN
        assert job.status == PublishingStatus.DRAFT
    
    def test_mark_published(self):
        """Test marking job as published."""
        job = PublishingJob(content_id="c1", channel=Channel.LINKEDIN)
        
        job.mark_published(external_post_id="post-123", external_url="https://linkedin.com/...")
        
        assert job.status == PublishingStatus.PUBLISHED
        assert job.external_post_id == "post-123"
        assert job.published_time is not None
    
    def test_mark_failed(self):
        """Test marking job as failed."""
        job = PublishingJob(content_id="c1", channel=Channel.LINKEDIN)
        job.mark_failed("API error", "Connection timeout")
        
        assert job.status == PublishingStatus.FAILED
        assert "API error" in job.error_message
    
    def test_metrics_tracking(self):
        """Test tracking metrics on job."""
        job = PublishingJob(content_id="c1", channel=Channel.LINKEDIN)
        
        job.set_metric(PublishingMetrics.IMPRESSIONS, 1000)
        job.set_metric(PublishingMetrics.ENGAGEMENTS, 50)
        
        assert job.get_metric(PublishingMetrics.IMPRESSIONS) == 1000
        assert job.get_metric(PublishingMetrics.ENGAGEMENTS) == 50


class TestPublishingCampaign:
    """Test PublishingCampaign model."""
    
    def test_campaign_creation(self):
        """Test creating campaign."""
        campaign = PublishingCampaign(
            name="Q1 Launch",
            description="Q1 product launch campaign"
        )
        assert campaign.name == "Q1 Launch"
        assert campaign.is_active == False
    
    def test_add_content(self):
        """Test adding content to campaign."""
        campaign = PublishingCampaign(name="Test Campaign")
        
        campaign.add_content("content-1")
        campaign.add_content("content-2")
        
        assert len(campaign.content_ids) == 2
    
    def test_add_channels(self):
        """Test adding channels."""
        campaign = PublishingCampaign(name="Test Campaign")
        
        for channel in [Channel.LINKEDIN, Channel.TWITTER]:
            campaign.add_channel(channel)
        
        assert len(campaign.channels) == 2


class TestPublishingPipeline:
    """Test publishing pipeline."""
    
    def setup_method(self):
        """Reset pipeline before each test."""
        reset_publishing_pipeline()
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes."""
        pipeline = get_publishing_pipeline()
        assert pipeline is not None
        assert pipeline.crm is not None
    
    def test_get_publishing_job(self):
        """Test retrieving publishing job."""
        pipeline = get_publishing_pipeline()
        
        job = PublishingJob(content_id="c1", channel=Channel.LINKEDIN)
        pipeline.publishing_jobs[job.job_id] = job
        
        retrieved = pipeline.get_publishing_job(job.job_id)
        assert retrieved is not None
        assert retrieved.content_id == "c1"


# Pytest async support
pytest_plugins = ('pytest_asyncio',)
