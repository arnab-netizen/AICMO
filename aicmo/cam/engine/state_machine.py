"""
CAM State Machine — Lead status transitions and next-action timing.

Phase 4: Encapsulates lead status transitions and computes next action times
based on campaign settings and enrichment/outreach events.

Uses extended fields from domain.py and db_models.py:
- lead_score (0.0-1.0)
- tags (list of categorical tags)
- last_contacted_at (datetime)
- next_action_at (datetime)
- last_reply_at (datetime)
- enrichment_data (dict)
"""

from datetime import datetime, timedelta
from typing import Optional

from aicmo.cam.domain import Lead, Campaign, LeadStatus, AttemptStatus


# ═══════════════════════════════════════════════════════════════════════
# STATUS TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════


def initial_status_for_new_lead(lead: Lead) -> LeadStatus:
    """
    Compute initial status for a newly discovered lead.
    
    Args:
        lead: Newly discovered lead
        
    Returns:
        LeadStatus.NEW for any new lead
    """
    return LeadStatus.NEW


def status_after_enrichment(lead: Lead) -> LeadStatus:
    """
    Compute lead status after enrichment (Apollo, Clearbit, etc.).
    
    If enrichment found valid data, mark as ENRICHED.
    Otherwise, keep status as-is (may be NEW or already enriched).
    
    Args:
        lead: Lead after enrichment attempt
        
    Returns:
        LeadStatus.ENRICHED if enrichment_data present, otherwise LeadStatus.NEW
    """
    if lead.enrichment_data and len(lead.enrichment_data) > 0:
        return LeadStatus.ENRICHED
    return LeadStatus.NEW


def status_after_outreach(
    lead: Lead,
    attempt_status: AttemptStatus,
    lead_score: Optional[float] = None,
) -> LeadStatus:
    """
    Compute lead status based on outreach attempt result.
    
    - SENT → CONTACTED
    - FAILED or SKIPPED → stays current status (don't mark as contacted)
    - If lead has high score or positive tags → QUALIFIED
    
    Args:
        lead: Lead after outreach attempt
        attempt_status: Result of the outreach attempt
        lead_score: Optional updated lead score
        
    Returns:
        Updated LeadStatus
    """
    # Update score if provided
    if lead_score is not None:
        lead.lead_score = lead_score
    
    # If send failed, don't advance status
    if attempt_status in (AttemptStatus.FAILED, AttemptStatus.SKIPPED):
        return lead.status if lead.status else LeadStatus.NEW
    
    # If send succeeded, mark as CONTACTED
    if attempt_status == AttemptStatus.SENT:
        # Check if lead is high quality (score > 0.7 or has "hot" tag)
        if lead.lead_score and lead.lead_score > 0.7:
            return LeadStatus.QUALIFIED
        if lead.tags and "hot" in lead.tags:
            return LeadStatus.QUALIFIED
        return LeadStatus.CONTACTED
    
    return lead.status if lead.status else LeadStatus.NEW


def should_stop_followup(lead: Lead, campaign: Campaign) -> bool:
    """
    Determine if we should stop following up on a lead.
    
    Stop followup if:
    - Lead status is LOST, QUALIFIED, or REPLIED
    - Lead has "do_not_contact" tag
    - Lead has been contacted but no reply for 30+ days
    
    Args:
        lead: Lead to check
        campaign: Campaign context
        
    Returns:
        True if we should stop followup, False otherwise
    """
    # Never follow up on these statuses
    if lead.status in (LeadStatus.LOST, LeadStatus.QUALIFIED, LeadStatus.REPLIED):
        return True
    
    # Check for do-not-contact tag
    if lead.tags and "do_not_contact" in lead.tags:
        return True
    
    # If contacted but no reply for 30+ days, stop
    if lead.last_contacted_at and not lead.last_reply_at:
        days_since_contact = (datetime.utcnow() - lead.last_contacted_at).days
        if days_since_contact > 30:
            return True
    
    return False


# ═══════════════════════════════════════════════════════════════════════
# TIMING LOGIC
# ═══════════════════════════════════════════════════════════════════════


def compute_next_action_time(
    lead: Lead,
    campaign: Campaign,
    now: datetime,
    action_type: str = "followup",
) -> datetime:
    """
    Compute when the next action should be taken on a lead.
    
    Timing rules:
    - NEW lead: immediate (now + 1 minute buffer)
    - ENRICHED lead: same day, offset by lead score (higher score = sooner)
    - CONTACTED lead: 3 days later for first followup
    - After 2+ followups: 7 days later
    - If has_replied: 1 day (quick response)
    
    Args:
        lead: Lead to schedule
        campaign: Campaign context (for channel info if needed)
        now: Current datetime
        action_type: Type of action ("enrichment", "followup", "reply", etc.)
        
    Returns:
        Datetime for next action
    """
    # Default: immediate
    next_action = now + timedelta(minutes=1)
    
    if action_type == "enrichment":
        # Enrich immediately after discovery
        return now + timedelta(seconds=30)
    
    elif action_type == "followup":
        # Base followup timing on current status
        if lead.status == LeadStatus.NEW:
            # New leads get contacted ASAP
            return now + timedelta(minutes=5)
        
        elif lead.status == LeadStatus.ENRICHED:
            # Enriched leads: score determines timing (0.0-1.0)
            # Low score (0.3) → 6 hours
            # High score (0.8) → 30 minutes
            if lead.lead_score:
                delay_minutes = max(30, int(360 * (1 - lead.lead_score)))
                return now + timedelta(minutes=delay_minutes)
            return now + timedelta(hours=1)
        
        elif lead.status == LeadStatus.CONTACTED:
            # Already contacted: wait 3 days before followup
            # Count previous attempts to space them out further
            attempt_count = len(lead.tags) if lead.tags else 0
            if "attempt_2" in (lead.tags or []):
                # 2nd+ followup: wait longer (7 days)
                return now + timedelta(days=7)
            else:
                # 1st followup: 3 days
                return now + timedelta(days=3)
        
        elif lead.status == LeadStatus.REPLIED:
            # Lead replied: respond quickly (1 day)
            return now + timedelta(days=1)
        
        else:
            # Default: 1 day
            return now + timedelta(days=1)
    
    elif action_type == "reply":
        # If lead replied, respond within 1 day (business hours)
        return now + timedelta(hours=24)
    
    else:
        # Unknown action type: default to 1 day
        return now + timedelta(days=1)


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════


def advance_attempt_count(lead: Lead) -> None:
    """
    Increment the attempt count tag on a lead.
    
    Tags used: "attempt_1", "attempt_2", "attempt_3", etc.
    
    Args:
        lead: Lead to update (in-place)
    """
    if not lead.tags:
        lead.tags = ["attempt_1"]
        return
    
    # Find existing attempt tag
    attempt_tags = [t for t in lead.tags if t.startswith("attempt_")]
    if attempt_tags:
        # Remove old tag, add incremented tag
        lead.tags = [t for t in lead.tags if not t.startswith("attempt_")]
        current_attempt = int(attempt_tags[0].split("_")[1])
        lead.tags.append(f"attempt_{current_attempt + 1}")
    else:
        # First attempt
        lead.tags.append("attempt_1")


def get_attempt_count(lead: Lead) -> int:
    """
    Get the number of outreach attempts made to a lead.
    
    Args:
        lead: Lead to check
        
    Returns:
        Number of attempts (0 if no attempts recorded)
    """
    if not lead.tags:
        return 0
    
    attempt_tags = [t for t in lead.tags if t.startswith("attempt_")]
    if attempt_tags:
        return int(attempt_tags[0].split("_")[1])
    
    return 0
