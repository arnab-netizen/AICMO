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

    publish_status: PublishStatus = PublishStatus.DRAFT
    external_id: Optional[str] = None
    last_error: Optional[str] = None
