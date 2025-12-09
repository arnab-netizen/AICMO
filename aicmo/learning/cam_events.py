"""
CAM (Customer Acquisition Module) learning events.

Tracks lead generation, outreach, qualification, and deal outcomes
to help Kaizen learn which acquisition patterns work best.
"""

from typing import Optional, Dict, Any
from aicmo.memory.engine import log_event


def log_lead_created(
    lead_id: int,
    source: str,
    project_id: Optional[str] = None,
    icp_match_score: Optional[float] = None,
    industry: Optional[str] = None,
    company_size: Optional[str] = None
) -> None:
    """
    Log new lead creation.
    
    Args:
        lead_id: Lead database ID
        source: Lead source (e.g., "linkedin_outbound", "inbound_form", "referral")
        project_id: Optional campaign/project identifier
        icp_match_score: Optional ICP fit score (0-100)
        industry: Optional industry classification
        company_size: Optional company size (e.g., "startup", "mid-market", "enterprise")
    """
    details = {
        "lead_id": lead_id,
        "source": source
    }
    
    if icp_match_score is not None:
        details["icp_match_score"] = icp_match_score
    if industry:
        details["industry"] = industry
    if company_size:
        details["company_size"] = company_size
    
    log_event(
        "LEAD_CREATED",
        project_id=project_id,
        details=details,
        tags=["cam", "lead", "acquisition", source]
    )


def log_outreach_sent(
    lead_id: int,
    channel: str,
    template_id: Optional[str] = None,
    project_id: Optional[str] = None,
    sequence_position: Optional[int] = None
) -> None:
    """
    Log outreach message sent.
    
    Args:
        lead_id: Lead database ID
        channel: Outreach channel (e.g., "email", "linkedin_dm", "twitter_dm")
        template_id: Optional template identifier
        project_id: Optional campaign identifier
        sequence_position: Optional position in sequence (1, 2, 3, etc.)
    """
    details = {
        "lead_id": lead_id,
        "channel": channel
    }
    
    if template_id:
        details["template_id"] = template_id
    if sequence_position is not None:
        details["sequence_position"] = sequence_position
    
    log_event(
        "OUTREACH_SENT",
        project_id=project_id,
        details=details,
        tags=["cam", "outreach", channel]
    )


def log_outreach_replied(
    lead_id: int,
    channel: str,
    intent: str,
    project_id: Optional[str] = None,
    sentiment: Optional[str] = None
) -> None:
    """
    Log outreach reply received.
    
    Args:
        lead_id: Lead database ID
        channel: Reply channel
        intent: Reply intent ("positive", "negative", "neutral", "question")
        project_id: Optional campaign identifier
        sentiment: Optional sentiment analysis result
    """
    details = {
        "lead_id": lead_id,
        "channel": channel,
        "intent": intent
    }
    
    if sentiment:
        details["sentiment"] = sentiment
    
    log_event(
        "OUTREACH_REPLIED",
        project_id=project_id,
        details=details,
        tags=["cam", "outreach", "reply", channel, f"intent:{intent}"]
    )


def log_lead_qualified(
    lead_id: int,
    project_id: Optional[str] = None,
    qualification_score: Optional[float] = None,
    qualified_by: Optional[str] = None,
    budget_range: Optional[str] = None,
    timeline: Optional[str] = None
) -> None:
    """
    Log lead qualified as sales-ready.
    
    Args:
        lead_id: Lead database ID
        project_id: Optional campaign identifier
        qualification_score: Optional BANT/qualification score
        qualified_by: Optional qualifier name/ID
        budget_range: Optional budget range
        timeline: Optional project timeline
    """
    details = {
        "lead_id": lead_id,
        "outcome": "qualified"
    }
    
    if qualification_score is not None:
        details["qualification_score"] = qualification_score
    if qualified_by:
        details["qualified_by"] = qualified_by
    if budget_range:
        details["budget_range"] = budget_range
    if timeline:
        details["timeline"] = timeline
    
    log_event(
        "LEAD_QUALIFIED",
        project_id=project_id,
        details=details,
        tags=["cam", "lead", "qualified"]
    )


def log_lead_lost(
    lead_id: int,
    reason: str,
    project_id: Optional[str] = None,
    stage: Optional[str] = None
) -> None:
    """
    Log lead lost/disqualified.
    
    Args:
        lead_id: Lead database ID
        reason: Loss reason (e.g., "budget", "timing", "no_response", "competitor")
        project_id: Optional campaign identifier
        stage: Optional stage where lost (e.g., "outreach", "qualification", "proposal")
    """
    details = {
        "lead_id": lead_id,
        "outcome": "lost",
        "reason": reason
    }
    
    if stage:
        details["stage"] = stage
    
    log_event(
        "LEAD_LOST",
        project_id=project_id,
        details=details,
        tags=["cam", "lead", "lost", f"reason:{reason}"]
    )


def log_deal_won(
    lead_id: int,
    deal_size: float,
    pack_sold: str,
    project_id: Optional[str] = None,
    days_to_close: Optional[int] = None,
    discount_applied: Optional[float] = None
) -> None:
    """
    Log deal won.
    
    Args:
        lead_id: Lead database ID
        deal_size: Deal value in currency
        pack_sold: Pack/product sold
        project_id: Optional campaign identifier
        days_to_close: Optional days from lead creation to close
        discount_applied: Optional discount percentage
    """
    details = {
        "lead_id": lead_id,
        "deal_size": deal_size,
        "pack_sold": pack_sold
    }
    
    if days_to_close is not None:
        details["days_to_close"] = days_to_close
    if discount_applied is not None:
        details["discount_applied"] = discount_applied
    
    log_event(
        "DEAL_WON",
        project_id=project_id,
        details=details,
        tags=["cam", "deal", "won", pack_sold]
    )


def log_appointment_scheduled(
    lead_id: int,
    appointment_type: str,
    project_id: Optional[str] = None,
    scheduled_days_out: Optional[int] = None
) -> None:
    """
    Log appointment/meeting scheduled.
    
    Args:
        lead_id: Lead database ID
        appointment_type: Type of appointment (e.g., "discovery", "demo", "proposal")
        project_id: Optional campaign identifier
        scheduled_days_out: Optional days until appointment
    """
    details = {
        "lead_id": lead_id,
        "appointment_type": appointment_type
    }
    
    if scheduled_days_out is not None:
        details["scheduled_days_out"] = scheduled_days_out
    
    log_event(
        "APPOINTMENT_SCHEDULED",
        project_id=project_id,
        details=details,
        tags=["cam", "appointment", appointment_type]
    )
