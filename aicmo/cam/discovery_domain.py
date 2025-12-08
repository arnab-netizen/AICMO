"""
CAM Phase 7 - Ethical Lead Discovery Domain Models.

Provides discovery capabilities across platforms with strict ToS compliance.
NO scraping, NO automation of forbidden behaviors.
"""

from typing import Optional
from enum import Enum
from datetime import datetime

from aicmo.domain.base import AicmoBaseModel


class Platform(str, Enum):
    """Supported platforms for ethical discovery."""
    
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    WEB = "web"  # External providers like Apollo


class DiscoveryCriteria(AicmoBaseModel):
    """
    Search criteria for discovering leads across platforms.
    
    All searches must respect platform ToS and use official APIs only.
    """
    
    platforms: list[Platform]
    keywords: list[str]
    location: Optional[str] = None
    role_contains: Optional[str] = None
    min_followers: Optional[int] = None
    recent_activity_days: Optional[int] = 30


class DiscoveryJob(AicmoBaseModel):
    """
    A discovery job tracks a single lead-finding operation.
    
    Jobs are created by operators, run asynchronously, and produce
    DiscoveredProfile results that can be converted to CAM leads.
    """
    
    id: Optional[int] = None
    name: str
    criteria: DiscoveryCriteria
    campaign_id: Optional[int] = None
    status: str = "PENDING"  # PENDING/RUNNING/DONE/FAILED
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DiscoveredProfile(AicmoBaseModel):
    """
    A single profile discovered during a search.
    
    Contains normalized data from any platform source.
    """
    
    id: Optional[int] = None
    job_id: Optional[int] = None
    platform: Platform
    handle: str
    profile_url: str
    display_name: str
    bio: Optional[str] = None
    followers: Optional[int] = None
    location: Optional[str] = None
    match_score: float = 0.5  # 0.0-1.0 relevance score
    discovered_at: Optional[datetime] = None
