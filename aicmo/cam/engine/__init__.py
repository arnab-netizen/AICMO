"""
CAM Engine — Core Client Acquisition Mode logic.

Phases 4-7: Complete autonomous client acquisition engine.

Modules:
- state_machine: Lead status transitions and next-action logic
- safety_limits: Rate limiting, daily caps, safety enforcement
- targets_tracker: Campaign goal tracking and metrics
- lead_pipeline: Lead discovery, deduplication, enrichment, scoring
- outreach_engine: Outreach scheduling and execution
"""

from aicmo.cam.engine.state_machine import (
    initial_status_for_new_lead,
    status_after_enrichment,
    status_after_outreach,
    should_stop_followup,
    compute_next_action_time,
)
from aicmo.cam.engine.safety_limits import (
    get_daily_email_limit,
    remaining_email_quota,
    can_send_email,
    register_email_sent,
)
from aicmo.cam.engine.targets_tracker import (
    compute_campaign_metrics,
    is_campaign_goal_met,
)
from aicmo.cam.engine.lead_pipeline import (
    fetch_and_insert_new_leads,
    enrich_and_score_leads,
)
from aicmo.cam.engine.outreach_engine import (
    schedule_due_outreach,
    execute_due_outreach,
)

__all__ = [
    # State machine
    "initial_status_for_new_lead",
    "status_after_enrichment",
    "status_after_outreach",
    "should_stop_followup",
    "compute_next_action_time",
    # Safety limits
    "get_daily_email_limit",
    "remaining_email_quota",
    "can_send_email",
    "register_email_sent",
    # Targets
    "compute_campaign_metrics",
    "is_campaign_goal_met",
    # Pipeline
    "fetch_and_insert_new_leads",
    "enrich_and_score_leads",
    # Outreach
    "schedule_due_outreach",
    "execute_due_outreach",
]
