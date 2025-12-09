"""
Intake quality and clarity learning events.

Tracks intake quality to learn which client types provide clear briefs
and which lead to successful projects.
"""

from typing import Optional, List, Dict, Any
from aicmo.memory.engine import log_event


def log_intake_clarity_scored(
    project_id: str,
    clarity_score: float,
    follow_up_questions_count: int,
    missing_fields: Optional[List[str]] = None,
    client_segment: Optional[str] = None,
    industry: Optional[str] = None
) -> None:
    """
    Log intake clarity assessment.
    
    The "garbage in killer" scores intake quality to identify
    which clients provide good briefs vs. need hand-holding.
    
    Args:
        project_id: Project/campaign identifier
        clarity_score: Clarity score (0-100, higher = clearer)
        follow_up_questions_count: Number of clarification questions needed
        missing_fields: Optional list of missing/unclear fields
        client_segment: Optional client classification
        industry: Optional industry
        
    Usage:
        log_intake_clarity_scored(
            project_id="proj_123",
            clarity_score=85.5,
            follow_up_questions_count=2,
            missing_fields=["target_audience_details", "budget_range"],
            client_segment="mid_market",
            industry="saas"
        )
    """
    details = {
        "clarity_score": clarity_score,
        "follow_up_questions_count": follow_up_questions_count
    }
    
    if missing_fields:
        details["missing_fields"] = missing_fields
        details["missing_fields_count"] = len(missing_fields)
    
    if client_segment:
        details["client_segment"] = client_segment
    if industry:
        details["industry"] = industry
    
    # Categorize clarity level
    if clarity_score >= 80:
        clarity_level = "excellent"
    elif clarity_score >= 60:
        clarity_level = "good"
    elif clarity_score >= 40:
        clarity_level = "needs_clarification"
    else:
        clarity_level = "poor"
    
    details["clarity_level"] = clarity_level
    
    log_event(
        "INTAKE_CLARITY_SCORED",
        project_id=project_id,
        details=details,
        tags=["intake", "clarity", clarity_level]
    )


def log_intake_clarification_requested(
    project_id: str,
    questions: List[str],
    blocking: bool = False,
    urgency: str = "normal"
) -> None:
    """
    Log clarification request sent to client.
    
    Args:
        project_id: Project identifier
        questions: List of clarification questions
        blocking: Whether project is blocked until answered
        urgency: Urgency level ("low", "normal", "high")
    """
    details = {
        "questions_count": len(questions),
        "questions": questions,
        "blocking": blocking,
        "urgency": urgency
    }
    
    log_event(
        "INTAKE_CLARIFICATION_REQUESTED",
        project_id=project_id,
        details=details,
        tags=["intake", "clarification", f"urgency:{urgency}"]
    )


def log_intake_clarification_received(
    project_id: str,
    response_time_hours: float,
    questions_answered: int,
    total_questions: int,
    clarity_improved: bool = True
) -> None:
    """
    Log clarification response received from client.
    
    Args:
        project_id: Project identifier
        response_time_hours: Hours between request and response
        questions_answered: Number of questions answered
        total_questions: Total questions asked
        clarity_improved: Whether clarity improved after response
    """
    details = {
        "response_time_hours": response_time_hours,
        "questions_answered": questions_answered,
        "total_questions": total_questions,
        "answer_rate": questions_answered / total_questions if total_questions > 0 else 0,
        "clarity_improved": clarity_improved
    }
    
    # Categorize response time
    if response_time_hours <= 4:
        response_speed = "fast"
    elif response_time_hours <= 24:
        response_speed = "normal"
    elif response_time_hours <= 72:
        response_speed = "slow"
    else:
        response_speed = "very_slow"
    
    details["response_speed"] = response_speed
    
    log_event(
        "INTAKE_CLARIFICATION_RECEIVED",
        project_id=project_id,
        details=details,
        tags=["intake", "clarification", "response", response_speed]
    )


def log_intake_blocked(
    project_id: str,
    blocked_days: int,
    reason: str,
    client_segment: Optional[str] = None
) -> None:
    """
    Log project blocked in INTAKE_CLARIFYING state for too long.
    
    Helps identify problematic clients or patterns that lead to stalls.
    
    Args:
        project_id: Project identifier
        blocked_days: Number of days blocked
        reason: Reason for block (e.g., "no_client_response", "unclear_requirements")
        client_segment: Optional client classification
    """
    details = {
        "blocked_days": blocked_days,
        "reason": reason
    }
    
    if client_segment:
        details["client_segment"] = client_segment
    
    log_event(
        "INTAKE_BLOCKED",
        project_id=project_id,
        details=details,
        tags=["intake", "blocked", reason]
    )


def log_intake_approved(
    project_id: str,
    final_clarity_score: float,
    total_clarification_rounds: int,
    days_to_approval: float,
    pack_selected: str
) -> None:
    """
    Log intake finally approved and ready for execution.
    
    Args:
        project_id: Project identifier
        final_clarity_score: Final clarity score after all clarifications
        total_clarification_rounds: Total back-and-forth rounds
        days_to_approval: Days from initial intake to approval
        pack_selected: Pack selected for execution
    """
    details = {
        "final_clarity_score": final_clarity_score,
        "total_clarification_rounds": total_clarification_rounds,
        "days_to_approval": days_to_approval,
        "pack_selected": pack_selected
    }
    
    # Categorize intake efficiency
    if total_clarification_rounds == 0:
        efficiency = "perfect"
    elif total_clarification_rounds <= 1:
        efficiency = "good"
    elif total_clarification_rounds <= 3:
        efficiency = "acceptable"
    else:
        efficiency = "problematic"
    
    details["efficiency"] = efficiency
    
    log_event(
        "INTAKE_APPROVED",
        project_id=project_id,
        details=details,
        tags=["intake", "approved", efficiency, pack_selected]
    )
