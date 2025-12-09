"""
Performance data ingestion module.

Allows importing real-world performance data to link generation → execution → outcomes.
Enables Kaizen to learn from actual performance metrics.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from aicmo.memory.engine import log_event


class PerformanceData(BaseModel):
    """Performance metrics for a piece of content or campaign."""
    
    content_id: Optional[int] = None  # Link to CreativeAssetDB
    execution_job_id: Optional[int] = None  # Link to ExecutionJobDB
    external_id: Optional[str] = None  # Platform post ID
    
    platform: str  # "instagram", "linkedin", "twitter", etc.
    
    # Metrics
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    engagements: Optional[int] = None
    shares: Optional[int] = None
    saves: Optional[int] = None
    comments: Optional[int] = None
    conversions: Optional[int] = None
    
    # Calculated rates
    ctr: Optional[float] = None  # Click-through rate
    engagement_rate: Optional[float] = None
    conversion_rate: Optional[float] = None
    
    # Business metrics
    revenue: Optional[float] = None
    cost: Optional[float] = None
    roas: Optional[float] = None  # Return on ad spend
    
    # Temporal data
    date: str  # ISO date string
    campaign_id: Optional[int] = None
    
    # Content attributes (for pattern analysis)
    content_type: Optional[str] = None  # "reel", "static", "carousel"
    hook_type: Optional[str] = None
    tone: Optional[str] = None
    length_words: Optional[int] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


def ingest_performance_data(
    performance: PerformanceData,
    project_id: Optional[str] = None
) -> None:
    """
    Ingest performance data and log as learning event.
    
    Links real-world performance back to generated content,
    enabling Kaizen to learn what works.
    
    Args:
        performance: Performance metrics
        project_id: Optional project identifier
        
    Usage:
        performance = PerformanceData(
            content_id=123,
            platform="instagram",
            impressions=5000,
            clicks=250,
            engagements=400,
            conversions=12,
            ctr=0.05,
            engagement_rate=0.08,
            conversion_rate=0.024,
            date="2025-12-08",
            content_type="reel",
            hook_type="question",
            tone="friendly"
        )
        ingest_performance_data(performance, project_id="campaign_456")
    """
    details = {
        "platform": performance.platform,
        "date": performance.date
    }
    
    # Add IDs for linking
    if performance.content_id:
        details["content_id"] = performance.content_id
    if performance.execution_job_id:
        details["execution_job_id"] = performance.execution_job_id
    if performance.external_id:
        details["external_id"] = performance.external_id
    if performance.campaign_id:
        details["campaign_id"] = performance.campaign_id
    
    # Add metrics
    metrics = {}
    if performance.impressions is not None:
        metrics["impressions"] = performance.impressions
    if performance.clicks is not None:
        metrics["clicks"] = performance.clicks
    if performance.engagements is not None:
        metrics["engagements"] = performance.engagements
    if performance.conversions is not None:
        metrics["conversions"] = performance.conversions
    if performance.ctr is not None:
        metrics["ctr"] = performance.ctr
    if performance.engagement_rate is not None:
        metrics["engagement_rate"] = performance.engagement_rate
    if performance.conversion_rate is not None:
        metrics["conversion_rate"] = performance.conversion_rate
    if performance.revenue is not None:
        metrics["revenue"] = performance.revenue
    if performance.roas is not None:
        metrics["roas"] = performance.roas
    
    details["metrics"] = metrics
    
    # Add content attributes for pattern learning
    attributes = {}
    if performance.content_type:
        attributes["content_type"] = performance.content_type
    if performance.hook_type:
        attributes["hook_type"] = performance.hook_type
    if performance.tone:
        attributes["tone"] = performance.tone
    if performance.length_words:
        attributes["length_words"] = performance.length_words
    
    if attributes:
        details["attributes"] = attributes
    
    if performance.metadata:
        details["metadata"] = performance.metadata
    
    # Calculate performance tier for tagging
    performance_tier = "unknown"
    if performance.engagement_rate is not None:
        if performance.engagement_rate >= 0.10:
            performance_tier = "excellent"
        elif performance.engagement_rate >= 0.05:
            performance_tier = "good"
        elif performance.engagement_rate >= 0.02:
            performance_tier = "average"
        else:
            performance_tier = "poor"
    
    tags = ["performance", performance.platform, performance_tier]
    
    if performance.content_type:
        tags.append(f"type:{performance.content_type}")
    if performance.hook_type:
        tags.append(f"hook:{performance.hook_type}")
    if performance.tone:
        tags.append(f"tone:{performance.tone}")
    
    log_event(
        "PERFORMANCE_RECORDED",
        project_id=project_id or f"campaign_{performance.campaign_id}" if performance.campaign_id else None,
        details=details,
        tags=tags
    )


def ingest_performance_batch(
    performances: List[PerformanceData],
    project_id: Optional[str] = None
) -> Dict[str, int]:
    """
    Ingest batch of performance data.
    
    Args:
        performances: List of performance metrics
        project_id: Optional project identifier
        
    Returns:
        Dict with ingestion stats
    """
    stats = {
        "total": len(performances),
        "succeeded": 0,
        "failed": 0
    }
    
    for performance in performances:
        try:
            ingest_performance_data(performance, project_id)
            stats["succeeded"] += 1
        except Exception as e:
            stats["failed"] += 1
            # Log ingestion failure
            log_event(
                "PERFORMANCE_INGESTION_FAILED",
                project_id=project_id,
                details={"error": str(e), "platform": performance.platform},
                tags=["performance", "error"]
            )
    
    return stats


def mark_creative_as_winner(
    content_id: int,
    reason: str,
    metrics: Dict[str, Any],
    project_id: Optional[str] = None
) -> None:
    """
    Mark a creative asset as a top performer.
    
    Used by Kaizen to identify winner patterns for future reference.
    
    Args:
        content_id: Creative asset ID
        reason: Why it's a winner (e.g., "top_10_percent_ctr", "highest_conversions")
        metrics: Performance metrics
        project_id: Optional project identifier
    """
    details = {
        "content_id": content_id,
        "reason": reason,
        "metrics": metrics
    }
    
    log_event(
        "CREATIVE_MARKED_WINNER",
        project_id=project_id,
        details=details,
        tags=["performance", "winner", "top_performer"]
    )


def mark_creative_as_loser(
    content_id: int,
    reason: str,
    metrics: Dict[str, Any],
    patterns_to_avoid: Optional[List[str]] = None,
    project_id: Optional[str] = None
) -> None:
    """
    Mark a creative asset as a poor performer.
    
    Used by Kaizen to identify patterns to avoid.
    
    Args:
        content_id: Creative asset ID
        reason: Why it's a loser (e.g., "bottom_10_percent_engagement", "zero_conversions")
        metrics: Performance metrics
        patterns_to_avoid: Optional list of patterns that contributed to poor performance
        project_id: Optional project identifier
    """
    details = {
        "content_id": content_id,
        "reason": reason,
        "metrics": metrics
    }
    
    if patterns_to_avoid:
        details["patterns_to_avoid"] = patterns_to_avoid
    
    log_event(
        "CREATIVE_MARKED_LOSER",
        project_id=project_id,
        details=details,
        tags=["performance", "loser", "avoid_pattern"]
    )
