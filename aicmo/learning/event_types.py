"""
Event type constants for AICMO Learning / Kaizen system.

All subsystems emit events through aicmo.memory.engine.log_event()
using these standardized event type strings.

Stage L0: Extended for new subsystems (Pitch, Brand, Media, Advanced Creatives,
Social Intelligence, Analytics, Client Portal, PM).
"""

from enum import Enum


class EventType(str, Enum):
    """
    Standardized event types for AICMO learning system.
    
    Each event type represents a significant system action that should be
    learned from for continuous improvement.
    """
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXISTING EVENTS (Stage 0-4 baseline)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Strategy events
    STRATEGY_GENERATED = "STRATEGY_GENERATED"
    STRATEGY_FAILED = "STRATEGY_FAILED"
    
    # Creative events
    CREATIVES_GENERATED = "CREATIVES_GENERATED"
    CREATIVE_MARKED_WINNER = "CREATIVE_MARKED_WINNER"
    CREATIVE_MARKED_LOSER = "CREATIVE_MARKED_LOSER"
    
    # Execution events
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    
    # Pack events
    PACK_STARTED = "PACK_STARTED"
    PACK_COMPLETED = "PACK_COMPLETED"
    PACK_FAILED = "PACK_FAILED"
    SECTION_GENERATED = "SECTION_GENERATED"
    SECTION_FAILED = "SECTION_FAILED"
    PACK_QUALITY_ASSESSED = "PACK_QUALITY_ASSESSED"
    PACK_QUALITY_PASSED = "PACK_QUALITY_PASSED"
    PACK_QUALITY_FAILED = "PACK_QUALITY_FAILED"
    
    # CAM (Customer Acquisition) events
    LEAD_CREATED = "LEAD_CREATED"
    OUTREACH_SENT = "OUTREACH_SENT"
    OUTREACH_REPLIED = "OUTREACH_REPLIED"
    LEAD_QUALIFIED = "LEAD_QUALIFIED"
    LEAD_LOST = "LEAD_LOST"
    DEAL_WON = "DEAL_WON"
    APPOINTMENT_SCHEDULED = "APPOINTMENT_SCHEDULED"
    
    # Intake events
    INTAKE_CLARITY_SCORED = "INTAKE_CLARITY_SCORED"
    INTAKE_CLARIFICATION_REQUESTED = "INTAKE_CLARIFICATION_REQUESTED"
    INTAKE_CLARIFICATION_RECEIVED = "INTAKE_CLARIFICATION_RECEIVED"
    INTAKE_BLOCKED = "INTAKE_BLOCKED"
    INTAKE_APPROVED = "INTAKE_APPROVED"
    
    # Performance events
    PERFORMANCE_RECORDED = "PERFORMANCE_RECORDED"
    PERFORMANCE_INGESTION_FAILED = "PERFORMANCE_INGESTION_FAILED"
    
    # ═══════════════════════════════════════════════════════════════════════
    # NEW EVENTS (Stage L0: New Subsystems)
    # ═══════════════════════════════════════════════════════════════════════
    
    # Pitch & Proposal Engine events
    PITCH_CREATED = "PITCH_CREATED"
    PITCH_WON = "PITCH_WON"
    PITCH_LOST = "PITCH_LOST"
    PITCH_DECK_GENERATED = "PITCH_DECK_GENERATED"
    PROPOSAL_GENERATED = "PROPOSAL_GENERATED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    PROPOSAL_ACCEPTED = "PROPOSAL_ACCEPTED"
    PROPOSAL_REJECTED = "PROPOSAL_REJECTED"
    
    # Brand Strategy Engine events
    BRAND_ARCHITECTURE_GENERATED = "BRAND_ARCHITECTURE_GENERATED"
    BRAND_NARRATIVE_GENERATED = "BRAND_NARRATIVE_GENERATED"
    BRAND_POSITIONING_GENERATED = "BRAND_POSITIONING_GENERATED"
    BRAND_CORE_GENERATED = "BRAND_CORE_GENERATED"
    
    # Media Buying & Optimization Engine events
    MEDIA_PLAN_CREATED = "MEDIA_PLAN_CREATED"
    MEDIA_CAMPAIGN_CREATED = "MEDIA_CAMPAIGN_CREATED"
    MEDIA_CAMPAIGN_OPTIMIZED = "MEDIA_CAMPAIGN_OPTIMIZED"
    MEDIA_BUDGET_ALLOCATED = "MEDIA_BUDGET_ALLOCATED"
    MEDIA_PERFORMANCE_ANALYZED = "MEDIA_PERFORMANCE_ANALYZED"
    
    # Advanced Creative Production events
    ADV_CREATIVE_VIDEO_GENERATED = "ADV_CREATIVE_VIDEO_GENERATED"
    ADV_CREATIVE_MOTION_GENERATED = "ADV_CREATIVE_MOTION_GENERATED"
    ADV_CREATIVE_MOODBOARD_GENERATED = "ADV_CREATIVE_MOODBOARD_GENERATED"
    ADV_CREATIVE_STORYBOARD_GENERATED = "ADV_CREATIVE_STORYBOARD_GENERATED"
    ADV_CREATIVE_SCRIPT_GENERATED = "ADV_CREATIVE_SCRIPT_GENERATED"
    
    # Social Intelligence Engine events
    SOCIAL_INTEL_TREND_DETECTED = "SOCIAL_INTEL_TREND_DETECTED"
    SOCIAL_INTEL_INFLUENCER_FOUND = "SOCIAL_INTEL_INFLUENCER_FOUND"
    SOCIAL_INTEL_SENTIMENT_ANALYZED = "SOCIAL_INTEL_SENTIMENT_ANALYZED"
    SOCIAL_INTEL_CONVERSATION_TRACKED = "SOCIAL_INTEL_CONVERSATION_TRACKED"
    
    # Analytics & Attribution events
    ANALYTICS_REPORT_GENERATED = "ANALYTICS_REPORT_GENERATED"
    MMM_MODEL_UPDATED = "MMM_MODEL_UPDATED"
    ATTRIBUTION_CALCULATED = "ATTRIBUTION_CALCULATED"
    CHANNEL_PERFORMANCE_ANALYZED = "CHANNEL_PERFORMANCE_ANALYZED"
    ROAS_CALCULATED = "ROAS_CALCULATED"
    
    # Client Portal & Approvals events
    CLIENT_APPROVAL_REQUESTED = "CLIENT_APPROVAL_REQUESTED"
    CLIENT_APPROVAL_RESPONDED = "CLIENT_APPROVAL_RESPONDED"
    CLIENT_APPROVAL_APPROVED = "CLIENT_APPROVAL_APPROVED"
    CLIENT_APPROVAL_REJECTED = "CLIENT_APPROVAL_REJECTED"
    CLIENT_COMMENT_RECEIVED = "CLIENT_COMMENT_RECEIVED"
    CLIENT_PORTAL_ACCESSED = "CLIENT_PORTAL_ACCESSED"
    
    # Project & Resource Management events
    PM_TASK_SCHEDULED = "PM_TASK_SCHEDULED"
    PM_TASK_COMPLETED = "PM_TASK_COMPLETED"
    PM_TASK_DELAYED = "PM_TASK_DELAYED"
    PM_CAPACITY_ALERT = "PM_CAPACITY_ALERT"
    PM_RESOURCE_ALLOCATED = "PM_RESOURCE_ALLOCATED"
    PM_MILESTONE_REACHED = "PM_MILESTONE_REACHED"


# Convenience groupings for filtering/analysis
EVENT_GROUPS = {
    "strategy": [
        EventType.STRATEGY_GENERATED,
        EventType.STRATEGY_FAILED,
    ],
    "creatives": [
        EventType.CREATIVES_GENERATED,
        EventType.CREATIVE_MARKED_WINNER,
        EventType.CREATIVE_MARKED_LOSER,
    ],
    "execution": [
        EventType.EXECUTION_STARTED,
        EventType.EXECUTION_COMPLETED,
        EventType.EXECUTION_FAILED,
    ],
    "packs": [
        EventType.PACK_STARTED,
        EventType.PACK_COMPLETED,
        EventType.PACK_FAILED,
        EventType.SECTION_GENERATED,
        EventType.SECTION_FAILED,
        EventType.PACK_QUALITY_ASSESSED,
        EventType.PACK_QUALITY_PASSED,
        EventType.PACK_QUALITY_FAILED,
    ],
    "cam": [
        EventType.LEAD_CREATED,
        EventType.OUTREACH_SENT,
        EventType.OUTREACH_REPLIED,
        EventType.LEAD_QUALIFIED,
        EventType.LEAD_LOST,
        EventType.DEAL_WON,
        EventType.APPOINTMENT_SCHEDULED,
    ],
    "intake": [
        EventType.INTAKE_CLARITY_SCORED,
        EventType.INTAKE_CLARIFICATION_REQUESTED,
        EventType.INTAKE_CLARIFICATION_RECEIVED,
        EventType.INTAKE_BLOCKED,
        EventType.INTAKE_APPROVED,
    ],
    "performance": [
        EventType.PERFORMANCE_RECORDED,
        EventType.PERFORMANCE_INGESTION_FAILED,
    ],
    "pitch": [
        EventType.PITCH_CREATED,
        EventType.PITCH_WON,
        EventType.PITCH_LOST,
        EventType.PITCH_DECK_GENERATED,
        EventType.PROPOSAL_GENERATED,
        EventType.PROPOSAL_SENT,
        EventType.PROPOSAL_ACCEPTED,
        EventType.PROPOSAL_REJECTED,
    ],
    "brand": [
        EventType.BRAND_ARCHITECTURE_GENERATED,
        EventType.BRAND_NARRATIVE_GENERATED,
        EventType.BRAND_POSITIONING_GENERATED,
        EventType.BRAND_CORE_GENERATED,
    ],
    "media": [
        EventType.MEDIA_PLAN_CREATED,
        EventType.MEDIA_CAMPAIGN_CREATED,
        EventType.MEDIA_CAMPAIGN_OPTIMIZED,
        EventType.MEDIA_BUDGET_ALLOCATED,
        EventType.MEDIA_PERFORMANCE_ANALYZED,
    ],
    "advanced_creatives": [
        EventType.ADV_CREATIVE_VIDEO_GENERATED,
        EventType.ADV_CREATIVE_MOTION_GENERATED,
        EventType.ADV_CREATIVE_MOODBOARD_GENERATED,
        EventType.ADV_CREATIVE_STORYBOARD_GENERATED,
        EventType.ADV_CREATIVE_SCRIPT_GENERATED,
    ],
    "social_intel": [
        EventType.SOCIAL_INTEL_TREND_DETECTED,
        EventType.SOCIAL_INTEL_INFLUENCER_FOUND,
        EventType.SOCIAL_INTEL_SENTIMENT_ANALYZED,
        EventType.SOCIAL_INTEL_CONVERSATION_TRACKED,
    ],
    "analytics": [
        EventType.ANALYTICS_REPORT_GENERATED,
        EventType.MMM_MODEL_UPDATED,
        EventType.ATTRIBUTION_CALCULATED,
        EventType.CHANNEL_PERFORMANCE_ANALYZED,
        EventType.ROAS_CALCULATED,
    ],
    "client_portal": [
        EventType.CLIENT_APPROVAL_REQUESTED,
        EventType.CLIENT_APPROVAL_RESPONDED,
        EventType.CLIENT_APPROVAL_APPROVED,
        EventType.CLIENT_APPROVAL_REJECTED,
        EventType.CLIENT_COMMENT_RECEIVED,
        EventType.CLIENT_PORTAL_ACCESSED,
    ],
    "pm": [
        EventType.PM_TASK_SCHEDULED,
        EventType.PM_TASK_COMPLETED,
        EventType.PM_TASK_DELAYED,
        EventType.PM_CAPACITY_ALERT,
        EventType.PM_RESOURCE_ALLOCATED,
        EventType.PM_MILESTONE_REACHED,
    ],
}


def get_events_by_group(group: str) -> list[EventType]:
    """
    Get all event types for a specific subsystem group.
    
    Args:
        group: Group name (e.g., "pitch", "brand", "media")
        
    Returns:
        List of EventType enums for that group
        
    Usage:
        >>> pitch_events = get_events_by_group("pitch")
        >>> assert EventType.PITCH_CREATED in pitch_events
    """
    return EVENT_GROUPS.get(group, [])


def is_success_event(event_type: EventType) -> bool:
    """
    Determine if an event type represents a successful outcome.
    
    Args:
        event_type: Event type to check
        
    Returns:
        True if event represents success
    """
    success_indicators = [
        "GENERATED", "COMPLETED", "WON", "APPROVED", "PASSED", 
        "ACCEPTED", "REACHED", "DETECTED", "FOUND"
    ]
    return any(indicator in event_type.value for indicator in success_indicators)


def is_failure_event(event_type: EventType) -> bool:
    """
    Determine if an event type represents a failure outcome.
    
    Args:
        event_type: Event type to check
        
    Returns:
        True if event represents failure
    """
    failure_indicators = [
        "FAILED", "LOST", "REJECTED", "DELAYED", "ALERT"
    ]
    return any(indicator in event_type.value for indicator in failure_indicators)
