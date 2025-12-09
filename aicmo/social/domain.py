"""Social intelligence domain models.

Stage S: Social Intelligence Engine
Skeleton implementation for social listening, trend analysis, and influencer tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from aicmo.domain.base import AicmoBaseModel


class SocialPlatform(str, Enum):
    """Social media platforms."""
    
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    PINTEREST = "pinterest"


class SentimentType(str, Enum):
    """Sentiment categories."""
    
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class TrendStrength(str, Enum):
    """Trend strength indicators."""
    
    EMERGING = "emerging"
    GROWING = "growing"
    PEAK = "peak"
    DECLINING = "declining"


class SocialMention(AicmoBaseModel):
    """
    A single social media mention.
    
    Stage S: Skeleton for tracking brand mentions.
    """
    
    mention_id: str
    platform: SocialPlatform
    brand_name: str
    
    # Content
    author: str
    author_handle: Optional[str] = None
    content: str
    url: Optional[str] = None
    
    # Engagement
    likes: int = 0
    shares: int = 0
    comments: int = 0
    reach: int = 0
    
    # Sentiment
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0  # -1.0 to 1.0
    
    # Metadata
    posted_at: datetime
    captured_at: datetime


class SocialTrend(AicmoBaseModel):
    """
    A trending topic or hashtag on social media.
    
    Stage S: Skeleton for trend tracking.
    """
    
    trend_id: str
    keyword: str
    hashtag: Optional[str] = None
    
    platforms: List[SocialPlatform] = []
    
    # Metrics
    volume: int = 0  # Number of mentions
    engagement_rate: float = 0.0
    strength: TrendStrength = TrendStrength.EMERGING
    
    # Context
    related_keywords: List[str] = []
    top_posts: List[str] = []  # URLs to top posts
    
    # Tracking
    first_seen: datetime
    last_updated: datetime
    peak_date: Optional[datetime] = None


class Influencer(AicmoBaseModel):
    """
    Social media influencer profile.
    
    Stage S: Skeleton for influencer tracking.
    """
    
    influencer_id: str
    name: str
    handle: str
    platform: SocialPlatform
    
    # Audience
    followers: int
    avg_engagement_rate: float = 0.0
    audience_demographics: Dict[str, Any] = {}
    
    # Content
    content_categories: List[str] = []
    posting_frequency: Optional[str] = None  # e.g., "daily", "weekly"
    
    # Relevance
    relevance_score: float = 0.0  # 0-100
    niche: Optional[str] = None
    
    # Contact
    email: Optional[str] = None
    contact_info: Optional[str] = None
    
    # Metadata
    last_analyzed: datetime


class SocialListeningReport(AicmoBaseModel):
    """
    Social listening report aggregating mentions and sentiment.
    
    Stage S: Skeleton for monitoring brand health.
    """
    
    report_id: str
    brand_name: str
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Aggregates
    total_mentions: int = 0
    positive_mentions: int = 0
    negative_mentions: int = 0
    neutral_mentions: int = 0
    
    # Sentiment
    avg_sentiment_score: float = 0.0
    sentiment_trend: str = "stable"  # improving, declining, stable
    
    # Engagement
    total_reach: int = 0
    total_engagement: int = 0
    
    # Platforms
    platform_breakdown: Dict[str, int] = {}  # Platform -> mention count
    
    # Top content
    top_positive_mentions: List[SocialMention] = []
    top_negative_mentions: List[SocialMention] = []
    
    # Generated
    generated_at: datetime


class TrendAnalysis(AicmoBaseModel):
    """
    Analysis of social trends relevant to a brand.
    
    Stage S: Skeleton for opportunity identification.
    """
    
    analysis_id: str
    brand_name: str
    industry: Optional[str] = None
    
    # Time range
    start_date: datetime
    end_date: datetime
    
    # Trends
    emerging_trends: List[SocialTrend] = []
    relevant_hashtags: List[str] = []
    
    # Opportunities
    content_opportunities: List[str] = []  # Suggested topics to cover
    trending_keywords: List[str] = []
    
    # Competitive
    competitor_mentions: Dict[str, int] = {}  # Competitor -> mention count
    
    # Generated
    generated_at: datetime


class InfluencerCampaign(AicmoBaseModel):
    """
    Influencer marketing campaign proposal.
    
    Stage S: Skeleton for influencer partnerships.
    """
    
    campaign_id: str
    brand_name: str
    campaign_name: str
    
    # Strategy
    target_audience: str
    campaign_objectives: List[str] = []
    platforms: List[SocialPlatform] = []
    
    # Influencers
    recommended_influencers: List[Influencer] = []
    budget_per_influencer: Dict[str, float] = {}  # influencer_id -> budget
    
    # Content
    content_guidelines: Optional[str] = None
    hashtags: List[str] = []
    
    # Timeline
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Status
    status: str = "draft"  # draft, active, completed
    
    created_at: datetime
