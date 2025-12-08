"""Execution domain models."""

from enum import Enum
from typing import Optional

from .base import AicmoBaseModel


class PublishStatus(str, Enum):
    """Content publishing status."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    QUEUED = "QUEUED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class CreativeVariant(AicmoBaseModel):
    """
    A specific creative variation for a platform.
    
    Phase 3: Represents platform-specific creative content
    with hooks, captions, and CTAs.
    """
    
    platform: str  # "instagram", "linkedin", "twitter", "email"
    format: str  # "reel", "post", "carousel", "thread", "subject_line"
    hook: str
    caption: Optional[str] = None
    cta: Optional[str] = None
    tone: Optional[str] = None  # "professional", "friendly", "bold"


class ContentItem(AicmoBaseModel):
    """
    Domain model for a piece of content to be published.
    
    Represents a single post, email, or other deliverable that
    will be executed through a gateway adapter.
    """

    id: Optional[int] = None
    project_id: Optional[int] = None
    platform: str  # e.g. "linkedin", "instagram", "email"
    title: Optional[str] = None
    body_text: str

    # Creative fields
    hook: Optional[str] = None
    caption: Optional[str] = None
    cta: Optional[str] = None
    asset_type: Optional[str] = None  # "reel", "static_post", "carousel"
    
    # Scheduling
    scheduled_date: Optional[str] = None
    theme: Optional[str] = None

    publish_status: PublishStatus = PublishStatus.DRAFT
    external_id: Optional[str] = None
    last_error: Optional[str] = None
