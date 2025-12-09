"""Social intelligence interface.

Stage S: Social Intelligence Engine
Abstract interface for social listening, trend analysis, and influencer discovery tools.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from aicmo.social.domain import (
    SocialMention,
    SocialTrend,
    Influencer,
    SocialPlatform,
)


class SocialIntelligence(ABC):
    """
    Abstract interface for social intelligence tools.
    
    Stage S: Skeleton interface - implement concrete adapters for:
    - Brandwatch (social listening)
    - Sprout Social (monitoring)
    - Hootsuite Insights (analytics)
    - BuzzSumo (content discovery)
    - Traackr (influencer discovery)
    - Meltwater (media monitoring)
    - etc.
    
    Future: Add real social intelligence tool integration here.
    """
    
    @abstractmethod
    def search_mentions(
        self,
        keywords: List[str],
        platforms: List[SocialPlatform],
        start_date: datetime,
        end_date: datetime,
        limit: int = 100
    ) -> List[SocialMention]:
        """
        Search for social media mentions.
        
        Args:
            keywords: Search keywords
            platforms: Platforms to search
            start_date: Search start date
            end_date: Search end date
            limit: Maximum mentions to return
            
        Returns:
            List of social mentions
            
        Raises:
            NotImplementedError: Stage S skeleton
        """
        raise NotImplementedError("Stage S: Social listening integration pending")
    
    @abstractmethod
    def analyze_sentiment(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of social media content.
        
        Args:
            text: Content to analyze
            
        Returns:
            Sentiment analysis results with score and category
            
        Raises:
            NotImplementedError: Stage S skeleton
        """
        raise NotImplementedError("Stage S: Sentiment analysis integration pending")
    
    @abstractmethod
    def discover_trends(
        self,
        industry: str,
        platforms: List[SocialPlatform],
        limit: int = 20
    ) -> List[SocialTrend]:
        """
        Discover trending topics and hashtags.
        
        Args:
            industry: Industry or category to filter trends
            platforms: Platforms to analyze
            limit: Maximum trends to return
            
        Returns:
            List of social trends
            
        Raises:
            NotImplementedError: Stage S skeleton
        """
        raise NotImplementedError("Stage S: Trend discovery integration pending")
    
    @abstractmethod
    def find_influencers(
        self,
        niche: str,
        platforms: List[SocialPlatform],
        min_followers: int = 10000,
        limit: int = 50
    ) -> List[Influencer]:
        """
        Find relevant influencers for a brand.
        
        Args:
            niche: Influencer niche or category
            platforms: Platforms to search
            min_followers: Minimum follower count
            limit: Maximum influencers to return
            
        Returns:
            List of influencers
            
        Raises:
            NotImplementedError: Stage S skeleton
        """
        raise NotImplementedError("Stage S: Influencer discovery integration pending")
    
    @abstractmethod
    def get_engagement_metrics(
        self,
        url: str
    ) -> Dict[str, int]:
        """
        Get engagement metrics for a social media post.
        
        Args:
            url: URL of the post
            
        Returns:
            Engagement metrics (likes, shares, comments, etc.)
            
        Raises:
            NotImplementedError: Stage S skeleton
        """
        raise NotImplementedError("Stage S: Engagement tracking integration pending")
    
    @abstractmethod
    def track_competitors(
        self,
        competitor_handles: List[str],
        platforms: List[SocialPlatform],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Track competitor social media activity.
        
        Args:
            competitor_handles: List of competitor social handles
            platforms: Platforms to monitor
            start_date: Tracking start date
            end_date: Tracking end date
            
        Returns:
            Competitor activity analysis
            
        Raises:
            NotImplementedError: Stage S skeleton
        """
        raise NotImplementedError("Stage S: Competitor tracking integration pending")
