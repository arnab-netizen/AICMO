"""Media buying and optimization service.

Stage M: Media Buying & Optimization Engine
Stage K2: Enhanced with Kaizen-based channel allocation
Service layer for generating media plans and optimization recommendations.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from aicmo.domain.intake import ClientIntake
from aicmo.media.domain import (
    MediaCampaignPlan,
    MediaChannel,
    MediaChannelType,
    MediaObjective,
    MediaOptimizationAction,
    OptimizationActionType,
    MediaPerformanceSnapshot,
)
from aicmo.memory.engine import log_event
from aicmo.learning.event_types import EventType
from aicmo.learning.domain import KaizenContext

logger = logging.getLogger(__name__)


def generate_media_plan(
    intake: ClientIntake,
    total_budget: float,
    duration_days: int = 30,
    kaizen: Optional[KaizenContext] = None
) -> MediaCampaignPlan:
    """
    Generate a media campaign plan from client intake.
    
    Stage M: Skeleton implementation with basic channel allocation logic.
    Stage K2: Uses Kaizen insights to favor/avoid channels based on history.
    Future: Integrate with ML models for optimal channel mix.
    
    Args:
        intake: Client intake data
        total_budget: Total campaign budget
        duration_days: Campaign duration in days
        kaizen: Optional Kaizen context with channel performance history
        
    Returns:
        MediaCampaignPlan with channel allocations
    """
    logger.info(f"Generating media plan for {intake.brand_name} with ${total_budget} budget")
    
    # Stage K2: Log Kaizen influence
    if kaizen:
        logger.info(f"Kaizen: Applying insights from {len(kaizen.best_channels)} best channels, "
                   f"avoiding {len(kaizen.weak_channels)} weak channels")
    
    # Derive objective from intake goal
    objective = _map_goal_to_objective(intake)
    
    # Generate channel mix based on objective and Kaizen
    channels = _allocate_channels(total_budget, objective, kaizen)
    
    # Create campaign plan
    plan = MediaCampaignPlan(
        campaign_name=f"{intake.brand_name} - {objective.value.title()} Campaign",
        brand_name=intake.brand_name,
        objective=objective,
        total_budget=total_budget,
        flight_start=datetime.now(),
        flight_end=datetime.now() + timedelta(days=duration_days),
        channels=channels,
        target_audiences=intake.target_audiences or ["General audience"],
        key_messages=_derive_key_messages(intake),
        created_at=datetime.now(),
        plan_notes=f"Auto-generated for {intake.industry or 'general'} industry" +
                   (f" with Kaizen insights applied" if kaizen else "")
    )
    
    # Validate media plan before returning (G1: contracts layer)
    from aicmo.core.contracts import validate_media_plan
    plan = validate_media_plan(plan)
    
    # Learning: Log media plan creation
    log_event(
        EventType.MEDIA_PLAN_CREATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "total_budget": total_budget,
            "objective": objective.value,
            "num_channels": len(channels),
            "duration_days": duration_days,
            "kaizen_influenced": kaizen is not None,
            "channels": [ch.channel_type.value for ch in channels]
        },
        tags=["media", "planning", "campaign"]
    )
    
    logger.info(f"Generated media plan with {len(channels)} channels")
    return plan


def generate_optimization_actions(
    plan: MediaCampaignPlan,
    performance: Optional[MediaPerformanceSnapshot] = None,
    kaizen: Optional[KaizenContext] = None
) -> List[MediaOptimizationAction]:
    """
    Generate optimization recommendations for a media campaign.
    
    Stage M: Skeleton with basic rule-based recommendations.
    Stage K2: Considers historical channel performance from Kaizen.
    Future: Use ML to predict optimal actions based on historical performance.
    
    Args:
        plan: Current media campaign plan
        performance: Optional performance snapshot for analysis
        kaizen: Optional Kaizen context with optimization insights
        
    Returns:
        List of optimization actions
    """
    logger.info(f"Generating optimization actions for {plan.campaign_name}")
    
    actions: List[MediaOptimizationAction] = []
    
    # Stage M: Basic rule-based recommendations
    if performance:
        actions.extend(_performance_based_optimizations(plan, performance))
    else:
        actions.extend(_default_optimizations(plan))
    
    # Learning: Log optimization generation
    log_event(
        EventType.MEDIA_CAMPAIGN_OPTIMIZED.value,
        project_id=plan.brand_name,
        details={
            "campaign_name": plan.campaign_name,
            "num_actions": len(actions),
            "has_performance_data": performance is not None
        },
        tags=["media", "optimization", "campaign"]
    )
    
    logger.info(f"Generated {len(actions)} optimization actions")
    return actions


# ═══════════════════════════════════════════════════════════════════════
# Helper Functions (Stage M: Basic implementations)
# ═══════════════════════════════════════════════════════════════════════


def _map_goal_to_objective(intake: ClientIntake) -> MediaObjective:
    """Map intake goal to media objective."""
    goal = (intake.primary_goal or "").lower()
    
    if any(word in goal for word in ["awareness", "brand", "reach"]):
        return MediaObjective.AWARENESS
    elif any(word in goal for word in ["consideration", "engagement", "traffic"]):
        return MediaObjective.CONSIDERATION
    elif any(word in goal for word in ["conversion", "sales", "leads", "acquisition"]):
        return MediaObjective.CONVERSION
    elif any(word in goal for word in ["retention", "loyalty", "repeat"]):
        return MediaObjective.RETENTION
    
    return MediaObjective.AWARENESS  # Default


def _allocate_channels(
    total_budget: float, 
    objective: MediaObjective, 
    kaizen: Optional[KaizenContext] = None
) -> List[MediaChannel]:
    """
    Allocate budget across channels based on objective.
    
    Stage M: Simple allocation rules.
    Stage K2: Adjust allocations based on Kaizen channel performance.
    Future: ML-driven optimization.
    """
    channels: List[MediaChannel] = []
    
    # Stage K2: Build channel preference map from Kaizen
    channel_multipliers = {}
    if kaizen:
        # Boost best channels by 20%
        for best_ch in kaizen.best_channels:
            channel_multipliers[best_ch.lower()] = 1.2
        # Reduce weak channels by 30%
        for weak_ch in kaizen.weak_channels:
            channel_multipliers[weak_ch.lower()] = 0.7
    
    if objective == MediaObjective.AWARENESS:
        # Awareness: Display, Video, Social
        display_pct = 0.35
        video_pct = 0.35
        social_pct = 0.30
        
        # Stage K2: Adjust based on Kaizen
        if kaizen:
            if "youtube" in kaizen.best_channels or "video" in kaizen.best_channels:
                video_pct *= 1.2
                display_pct *= 0.9
                social_pct *= 0.9
            if "meta" in kaizen.best_channels or "social" in kaizen.best_channels:
                social_pct *= 1.2
                display_pct *= 0.9
                video_pct *= 0.9
            # Reduce weak channels
            if "display" in kaizen.weak_channels:
                display_pct *= 0.5
                video_pct *= 1.2
                social_pct *= 1.2
        
        # Normalize to sum to 1.0
        total_pct = display_pct + video_pct + social_pct
        display_pct /= total_pct
        video_pct /= total_pct
        social_pct /= total_pct
        
        channels.append(MediaChannel(
            channel_type=MediaChannelType.DISPLAY,
            budget_allocated=total_budget * display_pct,
            platform="Google Display Network"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.VIDEO,
            budget_allocated=total_budget * video_pct,
            platform="YouTube"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.SOCIAL,
            budget_allocated=total_budget * social_pct,
            platform="Meta"
        ))
    
    elif objective == MediaObjective.CONSIDERATION:
        # Consideration: Search, Social, Native
        channels.append(MediaChannel(
            channel_type=MediaChannelType.SEARCH,
            budget_allocated=total_budget * 0.40,
            platform="Google Ads"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.SOCIAL,
            budget_allocated=total_budget * 0.35,
            platform="Meta"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.NATIVE,
            budget_allocated=total_budget * 0.25,
            platform="Taboola"
        ))
    
    elif objective == MediaObjective.CONVERSION:
        # Conversion: Search, Programmatic, Social
        channels.append(MediaChannel(
            channel_type=MediaChannelType.SEARCH,
            budget_allocated=total_budget * 0.50,
            platform="Google Ads"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.PROGRAMMATIC,
            budget_allocated=total_budget * 0.30,
            platform="DV360"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.SOCIAL,
            budget_allocated=total_budget * 0.20,
            platform="Meta"
        ))
    
    else:  # RETENTION
        # Retention: Social, Display, Email (placeholder)
        channels.append(MediaChannel(
            channel_type=MediaChannelType.SOCIAL,
            budget_allocated=total_budget * 0.50,
            platform="Meta"
        ))
        channels.append(MediaChannel(
            channel_type=MediaChannelType.DISPLAY,
            budget_allocated=total_budget * 0.50,
            platform="Google Display Network"
        ))
    
    return channels


def _derive_key_messages(intake: ClientIntake) -> List[str]:
    """Derive key messages from intake."""
    messages = []
    
    if intake.primary_goal:
        messages.append(f"Achieve {intake.primary_goal.lower()}")
    
    if intake.product_service:
        messages.append(f"Featuring {intake.product_service}")
    
    if not messages:
        messages.append("Drive brand growth")
    
    return messages


def _performance_based_optimizations(
    plan: MediaCampaignPlan,
    performance: MediaPerformanceSnapshot
) -> List[MediaOptimizationAction]:
    """
    Generate optimizations based on performance data.
    
    Stage M: Basic rules. Future: ML-driven recommendations.
    """
    actions: List[MediaOptimizationAction] = []
    
    # Rule: If CTR is low, recommend creative rotation
    if performance.ctr < 0.01:  # < 1%
        for channel in plan.channels:
            actions.append(MediaOptimizationAction(
                action_type=OptimizationActionType.CREATIVE_ROTATION,
                channel_type=channel.channel_type,
                recommendation="Rotate in fresh creative assets",
                rationale=f"CTR below benchmark at {performance.ctr:.2%}",
                expected_impact="Increase CTR by 20-30%",
                priority="high",
                created_at=datetime.now()
            ))
    
    # Rule: If CPA is high, recommend bid adjustment
    if performance.cpa > 100:  # Arbitrary threshold
        for channel in plan.channels:
            actions.append(MediaOptimizationAction(
                action_type=OptimizationActionType.BID_ADJUSTMENT,
                channel_type=channel.channel_type,
                recommendation="Reduce bids to lower CPA",
                rationale=f"CPA above target at ${performance.cpa:.2f}",
                expected_impact="Reduce CPA by 15-25%",
                bid_change_percent=-15.0,
                priority="high",
                created_at=datetime.now()
            ))
    
    return actions


def _default_optimizations(plan: MediaCampaignPlan) -> List[MediaOptimizationAction]:
    """
    Generate default optimization recommendations.
    
    Stage M: Generic best practices. Future: Personalized to campaign.
    """
    actions: List[MediaOptimizationAction] = []
    
    # Generic: Suggest audience expansion after initial learning phase
    for channel in plan.channels:
        actions.append(MediaOptimizationAction(
            action_type=OptimizationActionType.AUDIENCE_EXPANSION,
            channel_type=channel.channel_type,
            recommendation="Expand to lookalike audiences",
            rationale="Initial campaign phase complete",
            expected_impact="Increase reach by 30-50%",
            priority="medium",
            created_at=datetime.now()
        ))
    
    return actions
