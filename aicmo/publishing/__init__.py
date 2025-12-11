"""
AICMO Phase 2: Publishing & Ads Execution Module

Multi-channel content distribution system that leverages:
- Phase 0: Multi-provider chains (social, email)
- Phase 1: CRM for contact targeting and engagement tracking

Key components:
- models: Content, PublishingJob, PublishingCampaign
- pipeline: Publishing orchestration across channels

Supported channels:
- LinkedIn, Twitter/X, Instagram (via SocialPoster chains)
- Email (via EmailSender chain)
- Website (future)

Usage:
    from aicmo.publishing import Content, Channel, publish_content
    
    # Create content
    content = Content(
        content_type=ContentType.SOCIAL_POST,
        title="New Product Launch",
        primary_content="Check out our new feature..."
    )
    
    # Add platform-specific versions
    for channel in [Channel.LINKEDIN, Channel.TWITTER]:
        version = ContentVersion(
            platform=channel,
            title="New Product",
            body="Multi-platform message"
        )
        content.add_version(version)
    
    # Publish
    jobs = await publish_content(content, [Channel.LINKEDIN, Channel.TWITTER])
"""

from aicmo.publishing.models import (
    ContentType,
    Channel,
    PublishingStatus,
    PublishingMetrics,
    ContentVersion,
    Content,
    PublishingJob,
    PublishingCampaign,
)

from aicmo.publishing.pipeline import (
    PublishingPipeline,
    get_publishing_pipeline,
    reset_publishing_pipeline,
    publish_content,
    publish_campaign,
)

__all__ = [
    # Enums
    "ContentType",
    "Channel",
    "PublishingStatus",
    "PublishingMetrics",
    # Models
    "ContentVersion",
    "Content",
    "PublishingJob",
    "PublishingCampaign",
    # Pipeline
    "PublishingPipeline",
    "get_publishing_pipeline",
    "reset_publishing_pipeline",
    # Convenience functions
    "publish_content",
    "publish_campaign",
]
