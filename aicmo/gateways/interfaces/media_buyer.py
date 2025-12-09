"""Media buyer interface.

Stage M: Media Buying & Optimization Engine
Abstract interface for media buying platforms (Google Ads, Meta, DV360, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from aicmo.media.domain import (
    MediaChannel,
    MediaCampaignPlan,
    MediaOptimizationAction,
    MediaPerformanceSnapshot,
)


class MediaBuyer(ABC):
    """
    Abstract interface for media buying platforms.
    
    Stage M: Skeleton interface - implement concrete adapters for:
    - Google Ads API
    - Meta Ads API
    - DV360 API
    - Trade Desk API
    - etc.
    
    Future: Add real platform integration here.
    """
    
    @abstractmethod
    def create_campaign(
        self,
        plan: MediaCampaignPlan,
        channel: MediaChannel
    ) -> str:
        """
        Create a campaign in the media platform.
        
        Args:
            plan: Media campaign plan
            channel: Specific channel configuration
            
        Returns:
            Platform campaign ID
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
    
    @abstractmethod
    def update_campaign_budget(
        self,
        campaign_id: str,
        new_budget: float
    ) -> bool:
        """
        Update campaign budget in the platform.
        
        Args:
            campaign_id: Platform campaign ID
            new_budget: New budget amount
            
        Returns:
            Success status
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
    
    @abstractmethod
    def apply_optimization(
        self,
        campaign_id: str,
        action: MediaOptimizationAction
    ) -> bool:
        """
        Apply an optimization action to a campaign.
        
        Args:
            campaign_id: Platform campaign ID
            action: Optimization action to apply
            
        Returns:
            Success status
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
    
    @abstractmethod
    def fetch_performance(
        self,
        campaign_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> MediaPerformanceSnapshot:
        """
        Fetch campaign performance data from platform.
        
        Args:
            campaign_id: Platform campaign ID
            start_date: Start of reporting period
            end_date: End of reporting period
            
        Returns:
            Performance snapshot
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
    
    @abstractmethod
    def get_available_audiences(self) -> List[Dict[str, Any]]:
        """
        Get available audience segments from platform.
        
        Returns:
            List of audience segment metadata
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
    
    @abstractmethod
    def pause_campaign(self, campaign_id: str) -> bool:
        """
        Pause a campaign in the platform.
        
        Args:
            campaign_id: Platform campaign ID
            
        Returns:
            Success status
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
    
    @abstractmethod
    def reactivate_campaign(self, campaign_id: str) -> bool:
        """
        Reactivate a paused campaign.
        
        Args:
            campaign_id: Platform campaign ID
            
        Returns:
            Success status
            
        Raises:
            NotImplementedError: Stage M skeleton
        """
        raise NotImplementedError("Stage M: Media buyer integration pending")
