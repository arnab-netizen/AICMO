"""Phase 2: Publishing Content Distribution Models"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid

class ContentType(Enum):
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    EMAIL_TEMPLATE = "email_template"

class Channel(Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    WEBSITE = "website"

class PublishingStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"

class PublishingMetrics(Enum):
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    ENGAGEMENTS = "engagements"
    CONVERSIONS = "conversions"

@dataclass
class ContentVersion:
    platform: Channel
    title: str
    body: str
    description: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    cta_text: Optional[str] = None
    cta_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class Content:
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_type: ContentType = ContentType.SOCIAL_POST
    title: str = ""
    primary_content: str = ""
    platform_versions: Dict[Channel, ContentVersion] = field(default_factory=dict)
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    is_draft: bool = True
    is_approved: bool = False
    approval_notes: Optional[str] = None
    
    def get_version_for_platform(self, channel: Channel):
        return self.platform_versions.get(channel)
    
    def add_version(self, version: ContentVersion):
        self.platform_versions[version.platform] = version
        self.updated_at = datetime.now()
    
    def approve(self, notes: Optional[str] = None):
        self.is_approved = True
        self.is_draft = False
        self.approval_notes = notes

@dataclass
class PublishingJob:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str = ""
    channel: Channel = Channel.LINKEDIN
    status: PublishingStatus = PublishingStatus.DRAFT
    scheduled_time: Optional[datetime] = None
    published_time: Optional[datetime] = None
    external_post_id: Optional[str] = None
    external_url: Optional[str] = None
    metrics: Dict[PublishingMetrics, int] = field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def mark_published(self, external_post_id: Optional[str] = None, external_url: Optional[str] = None):
        self.status = PublishingStatus.PUBLISHED
        self.published_time = datetime.now()
        self.external_post_id = external_post_id
        self.external_url = external_url
    
    def mark_failed(self, error: str, details: Optional[str] = None):
        self.status = PublishingStatus.FAILED
        self.error_message = error
        if details:
            self.error_message += f": {details}"
    
    def get_metric(self, metric: PublishingMetrics) -> int:
        return self.metrics.get(metric, 0)
    
    def set_metric(self, metric: PublishingMetrics, value: int):
        self.metrics[metric] = value

@dataclass
class PublishingCampaign:
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    content_ids: List[str] = field(default_factory=list)
    channels: List[Channel] = field(default_factory=list)
    is_active: bool = False
    target_audience_ids: List[str] = field(default_factory=list)
    target_tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_content(self, content_id: str):
        if content_id not in self.content_ids:
            self.content_ids.append(content_id)
    
    def add_channel(self, channel: Channel):
        if channel not in self.channels:
            self.channels.append(channel)
    
    def activate(self):
        self.is_active = True
