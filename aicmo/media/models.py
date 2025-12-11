"""
Phase 4: Media Management Models

Dataclasses for media asset management, performance tracking, and reuse.
Integrates with Phase 2 publishing and Phase 3 analytics.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4
import hashlib


class MediaType(Enum):
    """Types of media assets."""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    INFOGRAPHIC = "infographic"
    THUMBNAIL = "thumbnail"
    BANNER = "banner"
    ICON = "icon"


class ImageFormat(Enum):
    """Image file formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    SVG = "svg"
    GIF = "gif"


class VideoFormat(Enum):
    """Video file formats."""
    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"
    MKV = "mkv"


class MediaStatus(Enum):
    """Status of media asset."""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class MediaDimensions:
    """Media dimensions in pixels."""
    width: int
    height: int
    
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width / height)."""
        if self.height == 0:
            return 0.0
        return self.width / self.height
    
    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass
class MediaMetadata:
    """Metadata for media asset."""
    file_size: int  # in bytes
    duration: Optional[int] = None  # in seconds, for videos
    format: Optional[str] = None
    color_count: Optional[int] = None  # for optimized images
    bitrate: Optional[int] = None  # for videos, in kbps
    frame_rate: Optional[int] = None  # for videos, in fps
    
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)


@dataclass
class MediaAsset:
    """Media asset (image, video, etc.)."""
    asset_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    media_type: MediaType = MediaType.IMAGE
    url: str = ""
    
    # Asset details
    dimensions: Optional[MediaDimensions] = None
    metadata: Optional[MediaMetadata] = None
    
    # Lifecycle
    uploaded_by: str = ""
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
    status: MediaStatus = MediaStatus.DRAFT
    is_approved: bool = False
    approval_notes: str = ""
    
    # Tracking
    content_hash: str = ""  # SHA256 hash for deduplication
    tags: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    
    # Usage
    usage_count: int = 0
    campaigns_used_in: Set[str] = field(default_factory=set)
    last_used_at: Optional[datetime] = None
    
    def compute_hash(self, file_data: bytes) -> str:
        """Compute SHA256 hash of file data."""
        self.content_hash = hashlib.sha256(file_data).hexdigest()
        return self.content_hash
    
    def add_tag(self, tag: str):
        """Add tag to asset."""
        self.tags.add(tag.lower())
    
    def add_category(self, category: str):
        """Add category to asset."""
        self.categories.add(category.lower())
    
    def mark_used(self, campaign_id: str):
        """Record asset usage in campaign."""
        self.usage_count += 1
        self.campaigns_used_in.add(campaign_id)
        self.last_used_at = datetime.utcnow()
    
    def approve(self, notes: str = ""):
        """Approve asset for use."""
        self.is_approved = True
        self.status = MediaStatus.APPROVED
        self.approval_notes = notes


@dataclass
class MediaVariant:
    """Variant of a media asset (e.g., different sizes, formats)."""
    variant_id: str = field(default_factory=lambda: str(uuid4()))
    asset_id: str = ""
    name: str = ""
    
    # Variant details
    dimensions: Optional[MediaDimensions] = None
    format: Optional[str] = None
    url: str = ""
    
    # Metadata
    file_size: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Usage
    platform: Optional[str] = None  # Which platform/channel optimized for
    performance_score: float = 0.0  # 0-100, based on engagement metrics


@dataclass
class MediaLibrary:
    """Collection of media assets."""
    library_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    owner: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Assets
    assets: Dict[str, MediaAsset] = field(default_factory=dict)
    
    # Organization
    tags: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    
    # Statistics
    total_size_bytes: int = 0
    last_modified: datetime = field(default_factory=datetime.utcnow)
    
    def add_asset(self, asset: MediaAsset):
        """Add asset to library."""
        self.assets[asset.asset_id] = asset
        if asset.metadata:
            self.total_size_bytes += asset.metadata.file_size
        self.last_modified = datetime.utcnow()
    
    def remove_asset(self, asset_id: str):
        """Remove asset from library."""
        if asset_id in self.assets:
            asset = self.assets.pop(asset_id)
            if asset.metadata:
                self.total_size_bytes -= asset.metadata.file_size
            self.last_modified = datetime.utcnow()
    
    def get_asset(self, asset_id: str) -> Optional[MediaAsset]:
        """Get asset by ID."""
        return self.assets.get(asset_id)
    
    def get_assets_by_tag(self, tag: str) -> List[MediaAsset]:
        """Get all assets with tag."""
        return [
            asset for asset in self.assets.values()
            if tag.lower() in asset.tags
        ]
    
    def get_assets_by_category(self, category: str) -> List[MediaAsset]:
        """Get all assets in category."""
        return [
            asset for asset in self.assets.values()
            if category.lower() in asset.categories
        ]
    
    def get_most_used_assets(self, limit: int = 10) -> List[MediaAsset]:
        """Get most reused assets."""
        sorted_assets = sorted(
            self.assets.values(),
            key=lambda a: a.usage_count,
            reverse=True
        )
        return sorted_assets[:limit]
    
    def total_size_mb(self) -> float:
        """Get total library size in MB."""
        return self.total_size_bytes / (1024 * 1024)
    
    def asset_count(self) -> int:
        """Get total asset count."""
        return len(self.assets)


@dataclass
class MediaPerformance:
    """Performance metrics for a media asset in a campaign."""
    performance_id: str = field(default_factory=lambda: str(uuid4()))
    asset_id: str = ""
    campaign_id: str = ""
    channel: str = ""
    
    # Engagement metrics
    impressions: int = 0
    clicks: int = 0
    engagements: int = 0
    conversions: int = 0
    shares: int = 0
    comments: int = 0
    
    # Calculated metrics
    ctr: float = 0.0  # Click-through rate
    engagement_rate: float = 0.0
    conversion_rate: float = 0.0
    
    # Timing
    tracked_from: datetime = field(default_factory=datetime.utcnow)
    tracked_until: Optional[datetime] = None
    
    def calculate_rates(self):
        """Recalculate engagement rates."""
        if self.impressions > 0:
            self.ctr = self.clicks / self.impressions
            self.engagement_rate = self.engagements / self.impressions
        
        if self.clicks > 0:
            self.conversion_rate = self.conversions / self.clicks
    
    def is_high_performing(self, ctr_threshold: float = 0.05) -> bool:
        """Check if asset performs above threshold."""
        return self.ctr >= ctr_threshold


@dataclass
class MediaOptimizationSuggestion:
    """Suggestion for media optimization."""
    suggestion_id: str = field(default_factory=lambda: str(uuid4()))
    asset_id: str = ""
    
    # Suggestion details
    type: str = ""  # "resize", "compress", "reformat", "remove_bg", etc.
    description: str = ""
    priority: str = "medium"  # low, medium, high
    
    # Expected impact
    estimated_improvement: float = 0.0  # percentage
    estimated_file_size_reduction: Optional[float] = None  # percentage
    
    # Implementation
    is_applied: bool = False
    applied_at: Optional[datetime] = None
    new_asset_id: Optional[str] = None  # If creates new variant
