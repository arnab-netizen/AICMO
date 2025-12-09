"""Analytics platform interface.

Stage A: Analytics & Attribution Engine
Abstract interface for analytics platforms and data warehouses.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from aicmo.analytics.domain import (
    TouchPoint,
    ConversionEvent,
    ChannelType,
    MetricType,
)


class AnalyticsPlatform(ABC):
    """
    Abstract interface for analytics platforms.
    
    Stage A: Skeleton interface - implement concrete adapters for:
    - Google Analytics 4 (web analytics)
    - Adobe Analytics (enterprise analytics)
    - Segment (customer data platform)
    - Snowflake (data warehouse)
    - BigQuery (data warehouse)
    - Mixpanel (product analytics)
    - Amplitude (product analytics)
    - etc.
    
    Future: Add real analytics platform integration here.
    """
    
    @abstractmethod
    def fetch_touchpoints(
        self,
        customer_ids: Optional[List[str]],
        start_date: datetime,
        end_date: datetime
    ) -> List[TouchPoint]:
        """
        Fetch customer touchpoints from analytics platform.
        
        Args:
            customer_ids: List of customer IDs (None for all)
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            List of touchpoints
            
        Raises:
            NotImplementedError: Stage A skeleton
        """
        raise NotImplementedError("Stage A: Analytics platform integration pending")
    
    @abstractmethod
    def fetch_conversions(
        self,
        start_date: datetime,
        end_date: datetime,
        conversion_types: Optional[List[str]] = None
    ) -> List[ConversionEvent]:
        """
        Fetch conversion events from analytics platform.
        
        Args:
            start_date: Start date for conversions
            end_date: End date for conversions
            conversion_types: Types of conversions to fetch
            
        Returns:
            List of conversion events
            
        Raises:
            NotImplementedError: Stage A skeleton
        """
        raise NotImplementedError("Stage A: Conversion tracking integration pending")
    
    @abstractmethod
    def fetch_channel_metrics(
        self,
        channels: List[ChannelType],
        metrics: List[MetricType],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[str, float]]:
        """
        Fetch metrics for marketing channels.
        
        Args:
            channels: Channels to fetch metrics for
            metrics: Metrics to fetch
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            Nested dict: channel -> metric -> value
            
        Raises:
            NotImplementedError: Stage A skeleton
        """
        raise NotImplementedError("Stage A: Channel metrics integration pending")
    
    @abstractmethod
    def run_custom_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a custom analytics query.
        
        Args:
            query: Query string (SQL, GA4 query language, etc.)
            parameters: Query parameters
            
        Returns:
            Query results as list of dicts
            
        Raises:
            NotImplementedError: Stage A skeleton
        """
        raise NotImplementedError("Stage A: Custom query integration pending")
    
    @abstractmethod
    def create_audience_segment(
        self,
        name: str,
        criteria: Dict[str, Any]
    ) -> str:
        """
        Create an audience segment for targeting.
        
        Args:
            name: Segment name
            criteria: Segmentation criteria
            
        Returns:
            Segment ID
            
        Raises:
            NotImplementedError: Stage A skeleton
        """
        raise NotImplementedError("Stage A: Audience segmentation integration pending")
    
    @abstractmethod
    def get_real_time_metrics(
        self,
        metrics: List[MetricType]
    ) -> Dict[str, float]:
        """
        Get real-time metric values.
        
        Args:
            metrics: Metrics to fetch
            
        Returns:
            Dict of metric -> current value
            
        Raises:
            NotImplementedError: Stage A skeleton
        """
        raise NotImplementedError("Stage A: Real-time metrics integration pending")
