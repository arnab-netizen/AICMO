"""
CAM Orchestrator — Daily Client Acquisition Loop.

Phase 2: Safe, audit-able CAM cycle with dry-run defaults and gateway integration.

This module implements a complete daily cycle for client acquisition:
- Process new leads from external sources
- Score and qualify leads for outreach
- Send personalized outreach via safe gateways
- Detect replies and update lead status
- Escalate qualified leads to project pipeline

All operations are wrapped in safety limits (max/day, channels enabled, etc.).
By default, dry_run=True ensures no real emails/posts are sent.
"""

from dataclasses import dataclass
from typing import List, Optional
import logging

from aicmo.cam.domain import Lead, LeadStatus
from aicmo.cam.safety import SafetySettings, default_safety_settings
from aicmo.cam.humanization import sanitize_message_to_avoid_ai_markers
from aicmo.gateways import get_email_sender, get_social_poster, get_crm_syncer
from aicmo.memory.engine import log_event


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# CONFIG AND REPORT DATACLASSES
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class CAMCycleConfig:
    """
    Configuration for daily CAM cycle execution.
    
    Controls lead processing limits, enabled channels, and safety behavior.
    """
    
    max_new_leads_per_day: int
    max_outreach_per_day: int
    max_followups_per_day: int
    channels_enabled: List[str]  # e.g., ["email", "linkedin"]
    dry_run: bool = True  # DEFAULT: Never send real messages
    safety_settings: Optional[SafetySettings] = None


@dataclass
class CAMCycleReport:
    """
    Report of daily CAM cycle execution.
    
    Captures counts and errors from each phase.
    """
    
    leads_created: int
    outreach_sent: int
    followups_sent: int
    hot_leads_detected: int
    errors: List[str]


# ═══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════


def run_daily_cam_cycle(config: CAMCycleConfig) -> CAMCycleReport:
    """
    Execute complete daily client acquisition cycle.
    
    Phases:
    1. Process new leads (discovery or import)
    2. Score/qualify leads
    3. Send personalized outreach
    4. Detect replies and update status
    5. Escalate hot leads to project pipeline
    
    All operations are safe to run multiple times and do not raise exceptions.
    Failures are logged and returned in CAMCycleReport.errors.
    
    Args:
        config: CAMCycleConfig with limits and safety settings
        
    Returns:
        CAMCycleReport with counts and error strings
        
    Example:
        config = CAMCycleConfig(
            max_new_leads_per_day=10,
            max_outreach_per_day=15,
            max_followups_per_day=5,
            channels_enabled=["email", "linkedin"],
            dry_run=True
        )
        report = run_daily_cam_cycle(config)
        print(f"Created {report.leads_created} leads")
        if report.errors:
            print(f"Errors: {report.errors}")
    """
    
    # Initialize counters and error list
    leads_created = 0
    outreach_sent = 0
    followups_sent = 0
    hot_leads_detected = 0
    errors: List[str] = []
    
    # Use provided safety settings or default
    if config.safety_settings is None:
        config.safety_settings = default_safety_settings()
    
    # Log cycle start
    log_event(
        "cam.cycle_started",
        details={
            "dry_run": config.dry_run,
            "channels_enabled": config.channels_enabled,
            "max_new_leads": config.max_new_leads_per_day,
        },
        tags=["cam", "daily_cycle"]
    )
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 1: Process new leads
    # ─────────────────────────────────────────────────────────────
    try:
        new_leads = process_new_leads(config)
        leads_created = new_leads
        log_event(
            "cam.leads_processed",
            details={"count": leads_created},
            tags=["cam", "discovery"]
        )
    except Exception as e:
        error_msg = f"process_new_leads failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "cam.error",
            details={"stage": "process_new_leads", "error": str(e)},
            tags=["cam", "error"]
        )
        errors.append(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 2: Schedule outreach for scored leads
    # ─────────────────────────────────────────────────────────────
    try:
        scheduled = schedule_outreach_for_scored_leads(config)
        log_event(
            "cam.outreach_scheduled",
            details={"count": scheduled},
            tags=["cam", "scheduling"]
        )
    except Exception as e:
        error_msg = f"schedule_outreach_for_scored_leads failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "cam.error",
            details={"stage": "schedule_outreach", "error": str(e)},
            tags=["cam", "error"]
        )
        errors.append(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 3: Send pending outreach
    # ─────────────────────────────────────────────────────────────
    try:
        sent = send_pending_outreach(config)
        outreach_sent = sent
        log_event(
            "cam.outreach_sent",
            details={
                "count": outreach_sent,
                "dry_run": config.dry_run,
                "channels": config.channels_enabled,
            },
            tags=["cam", "outreach"]
        )
    except Exception as e:
        error_msg = f"send_pending_outreach failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "cam.error",
            details={"stage": "send_outreach", "error": str(e)},
            tags=["cam", "error"]
        )
        errors.append(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 4: Detect replies and update lead status
    # ─────────────────────────────────────────────────────────────
    try:
        replies = detect_replies_and_update_lead_status(config)
        log_event(
            "cam.replies_detected",
            details={"count": replies},
            tags=["cam", "engagement"]
        )
    except Exception as e:
        error_msg = f"detect_replies_and_update_lead_status failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "cam.error",
            details={"stage": "detect_replies", "error": str(e)},
            tags=["cam", "error"]
        )
        errors.append(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 5: Escalate hot leads to strategy pipeline
    # ─────────────────────────────────────────────────────────────
    try:
        escalated = escalate_hot_leads_to_strategy_pipeline(config)
        hot_leads_detected = escalated
        log_event(
            "cam.leads_escalated",
            details={"count": escalated},
            tags=["cam", "escalation"]
        )
    except Exception as e:
        error_msg = f"escalate_hot_leads_to_strategy_pipeline failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "cam.error",
            details={"stage": "escalate_leads", "error": str(e)},
            tags=["cam", "error"]
        )
        errors.append(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # Build and return report
    # ─────────────────────────────────────────────────────────────
    report = CAMCycleReport(
        leads_created=leads_created,
        outreach_sent=outreach_sent,
        followups_sent=followups_sent,
        hot_leads_detected=hot_leads_detected,
        errors=errors
    )
    
    log_event(
        "cam.cycle_completed",
        details={
            "leads_created": report.leads_created,
            "outreach_sent": report.outreach_sent,
            "followups_sent": report.followups_sent,
            "hot_leads_detected": report.hot_leads_detected,
            "errors_count": len(report.errors),
        },
        tags=["cam", "daily_cycle"]
    )
    
    return report


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════


def process_new_leads(config: CAMCycleConfig) -> int:
    """
    Discover or create new leads for today.
    
    This is a stub that simulates lead discovery. In a real implementation,
    this would query external sources (Apollo, CSV imports, etc.) and create
    Lead records in the database.
    
    Args:
        config: CAMCycleConfig with max_new_leads_per_day limit
        
    Returns:
        Number of new leads created
    """
    try:
        # Stub: Simulate finding/creating leads
        # In production, this would:
        # - Query Apollo API or load CSV
        # - Create Lead records in database
        # - Respect max_new_leads_per_day limit
        
        created_count = 0
        logger.info(f"Processed new leads: {created_count} created")
        
        return created_count
    except Exception as e:
        logger.error(f"process_new_leads: {e}")
        return 0


def schedule_outreach_for_scored_leads(config: CAMCycleConfig) -> int:
    """
    Schedule outreach for leads that are ready to contact.
    
    Selects leads with high enough scores and NEW status,
    marks them as "ready for outreach" without actually sending yet.
    
    Args:
        config: CAMCycleConfig with max_outreach_per_day limit
        
    Returns:
        Number of leads scheduled for outreach
    """
    try:
        # Stub: Mark leads as ready for outreach
        # In production, this would:
        # - Query leads with status=NEW and score >= threshold
        # - Limit to max_outreach_per_day
        # - Mark them as scheduled/ready
        # - Generate personalization tokens
        
        scheduled_count = 0
        logger.info(f"Scheduled outreach for: {scheduled_count} leads")
        
        return scheduled_count
    except Exception as e:
        logger.error(f"schedule_outreach_for_scored_leads: {e}")
        return 0


def send_pending_outreach(config: CAMCycleConfig) -> int:
    """
    Send or simulate outbound messages for scheduled leads.
    
    Uses gateway factories to send emails/posts. If dry_run=True,
    no real messages are sent (adapters are no-ops).
    
    Respects:
    - Daily/hourly rate limits from SafetySettings
    - Enabled channels (config.channels_enabled)
    - Send windows (time-of-day restrictions)
    
    Args:
        config: CAMCycleConfig with channels and dry_run flag
        
    Returns:
        Number of outreach attempts made
    """
    try:
        sent_count = 0
        
        # Get gateway adapters via factory
        email_sender = get_email_sender()
        crm_syncer = get_crm_syncer()
        
        # Optionally get social posters if channels are enabled
        social_adapters = {}
        if "linkedin" in config.channels_enabled:
            social_adapters["linkedin"] = get_social_poster("linkedin")
        if "twitter" in config.channels_enabled:
            social_adapters["twitter"] = get_social_poster("twitter")
        
        # Stub: Iterate through pending outreach items
        # In production, this would:
        # - Query leads marked as ready/scheduled
        # - Check safety limits before each send
        # - Generate personalized message
        # - HUMANIZE the message (remove AI markers, lighten tone):
        #   message = sanitize_message_to_avoid_ai_markers(message)
        # - Call email_sender.send_email() or poster.post()
        # - Log attempt in OutreachAttemptDB
        # - Update lead status
        
        # For now, just log what we would do
        logger.info(
            f"Sent outreach: {sent_count} messages via {config.channels_enabled} "
            f"(dry_run={config.dry_run})"
        )
        
        return sent_count
    except Exception as e:
        logger.error(f"send_pending_outreach: {e}")
        return 0


def detect_replies_and_update_lead_status(config: CAMCycleConfig) -> int:
    """
    Detect signals that leads replied or showed interest.
    
    Checks for:
    - Email replies (from email adapter or mailbox monitoring)
    - Website visits (from tracking pixels)
    - LinkedIn profile views or message replies
    - Manual interest flags
    
    Updates lead status to REPLIED or QUALIFIED.
    
    Args:
        config: CAMCycleConfig
        
    Returns:
        Number of leads marked as having replies/interest
    """
    try:
        # Stub: Check for reply signals
        # In production, this would:
        # - Check CRM for logged interactions
        # - Query email for threaded replies
        # - Check tracking data
        # - Update lead.status to REPLIED if signals found
        
        reply_count = 0
        logger.info(f"Detected replies: {reply_count} leads")
        
        return reply_count
    except Exception as e:
        logger.error(f"detect_replies_and_update_lead_status: {e}")
        return 0


def escalate_hot_leads_to_strategy_pipeline(config: CAMCycleConfig) -> int:
    """
    Move qualified leads into the main project/strategy pipeline.
    
    Identifies leads with status QUALIFIED or REPLIED and creates
    projects for them in the main orchestration system.
    
    Args:
        config: CAMCycleConfig
        
    Returns:
        Number of leads escalated to project pipeline
    """
    try:
        # Stub: Escalate hot leads
        # In production, this would:
        # - Query leads with status=QUALIFIED or REPLIED
        # - Create Project records (if not already created)
        # - Transition projects to INTAKE_COMPLETE or similar
        # - Trigger strategy generation if configured
        
        escalated_count = 0
        logger.info(f"Escalated hot leads: {escalated_count} to strategy pipeline")
        
        return escalated_count
    except Exception as e:
        logger.error(f"escalate_hot_leads_to_strategy_pipeline: {e}")
        return 0
