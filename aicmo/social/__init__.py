"""Social intelligence module.

Stage S: Social Intelligence Engine
"""

from aicmo.social.domain import (
    SocialPlatform,
    SentimentType,
    TrendStrength,
    SocialMention,
    SocialTrend,
    Influencer,
    SocialListeningReport,
    TrendAnalysis,
    InfluencerCampaign,
)

from aicmo.social.service import (
    generate_listening_report,
    analyze_trends,
    discover_influencers,
    create_influencer_campaign,
)

__all__ = [
    # Enums
    "SocialPlatform",
    "SentimentType",
    "TrendStrength",
    
    # Domain models
    "SocialMention",
    "SocialTrend",
    "Influencer",
    "SocialListeningReport",
    "TrendAnalysis",
    "InfluencerCampaign",
    
    # Service functions
    "generate_listening_report",
    "analyze_trends",
    "discover_influencers",
    "create_influencer_campaign",
]
