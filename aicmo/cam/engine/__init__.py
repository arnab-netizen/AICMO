"""
CAM Engine — Core Client Acquisition Mode logic.

Phases 2-7: Complete autonomous client acquisition engine.

Modules:
- harvest_orchestrator: Multi-source lead harvesting with fallback chains (Phase 2)
- lead_scorer: ICP & opportunity scoring, tier classification (Phase 3)
- lead_qualifier: Email validation, intent detection, auto-qualification (Phase 4)
- lead_router: Route qualified leads to sequences based on tier (Phase 5)
- state_machine: Lead status transitions and next-action logic
- safety_limits: Rate limiting, daily caps, safety enforcement
- targets_tracker: Campaign goal tracking and metrics
- lead_pipeline: Lead discovery, deduplication, enrichment, scoring
- outreach_engine: Outreach scheduling and execution
"""

from aicmo.cam.engine.harvest_orchestrator import (
    HarvestOrchestrator,
    HarvestMetrics,
    run_harvest_batch,
)
from aicmo.cam.engine.lead_scorer import (
    ICPScorer,
    OpportunityScorer,
    TierClassifier,
    LeadTier,
    ScoringMetrics,
    batch_score_leads,
)
from aicmo.cam.engine.lead_qualifier import (
    QualificationRules,
    EmailQualifier,
    IntentDetector,
    LeadQualifier,
    QualificationStatus,
    RejectionReason,
    QualificationMetrics,
)
from aicmo.cam.engine.lead_router import (
    RoutingRules,
    ContentSequence,
    ContentSequenceType,
    LeadRouter,
    RoutingStatus,
    RoutingDecision,
    RoutingMetrics,
)
from aicmo.cam.engine.lead_nurture import (
    EmailTemplate,
    EngagementEvent,
    EngagementRecord,
    EngagementMetrics,
    EmailSendResult,
    NurtureScheduler,
    NurtureDecision,
    NurtureOrchestrator,
    NurtureMetrics,
)
from aicmo.cam.engine.continuous_cron import (
    CronScheduler,
    CronOrchestrator,
    JobResult,
    JobStatus,
    JobType,
    CronJobConfig,
    CronMetrics,
)
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
    # Phase 2: Lead Harvesting
    "HarvestOrchestrator",
    "HarvestMetrics",
    "run_harvest_batch",
    # Phase 3: Lead Scoring
    "ICPScorer",
    "OpportunityScorer",
    "TierClassifier",
    "LeadTier",
    "ScoringMetrics",
    "batch_score_leads",
    # Phase 4: Lead Qualification
    "QualificationRules",
    "EmailQualifier",
    "IntentDetector",
    "LeadQualifier",
    "QualificationStatus",
    "RejectionReason",
    "QualificationMetrics",
    # Phase 5: Lead Routing
    "RoutingRules",
    "ContentSequence",
    "ContentSequenceType",
    "LeadRouter",
    "RoutingStatus",
    "RoutingDecision",
    "RoutingMetrics",
    # Phase 6: Lead Nurture
    "EmailTemplate",
    "EngagementEvent",
    "EngagementRecord",
    "EngagementMetrics",
    "EmailSendResult",
    "NurtureScheduler",
    "NurtureDecision",
    "NurtureOrchestrator",
    "NurtureMetrics",
    # Phase 7: Continuous Cron
    "CronScheduler",
    "CronOrchestrator",
    "JobResult",
    "JobStatus",
    "JobType",
    "CronJobConfig",
    "CronMetrics",
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
