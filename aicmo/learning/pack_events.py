"""
Pack-level learning helpers.

Provides convenient helpers for logging learning events from pack execution,
ensuring all pack types hit the learning bus consistently.
"""

from typing import Optional, Dict, Any, List
from aicmo.memory.engine import log_event


def log_pack_event(
    event_type: str,
    pack_key: str,
    project_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a pack execution event.
    
    Standardized helper for logging events from any pack type:
    - Strategy-only packs
    - Full funnel packs
    - Launch/GTM packs
    - Audit/turnaround packs
    - Quick social packs
    
    Args:
        event_type: Type of event (e.g., "PACK_STARTED", "PACK_COMPLETED", "SECTION_GENERATED")
        pack_key: Pack identifier (e.g., "quick_social_basic", "full_funnel_growth_suite")
        project_id: Optional project/campaign identifier
        input_data: Optional dict of input parameters (brief, industry, etc.)
        output_data: Optional dict of output metrics (sections_count, quality_score, etc.)
        meta: Optional additional metadata
        
    Usage:
        log_pack_event(
            "PACK_STARTED",
            pack_key="quick_social_basic",
            project_id="campaign_123",
            input_data={"industry": "tech", "audience": "developers"}
        )
        
        log_pack_event(
            "PACK_COMPLETED",
            pack_key="full_funnel_growth_suite",
            project_id="campaign_456",
            output_data={"sections_generated": 23, "duration_seconds": 45.2}
        )
    """
    details = {"pack_key": pack_key}
    
    if input_data:
        details["input"] = input_data
    if output_data:
        details["output"] = output_data
    if meta:
        details["meta"] = meta
    
    tags = ["pack", pack_key, event_type.lower()]
    
    # Add pack type classification tags
    if "quick_social" in pack_key:
        tags.append("pack_type:quick_social")
    elif "strategy_campaign" in pack_key:
        tags.append("pack_type:strategy_campaign")
    elif "full_funnel" in pack_key:
        tags.append("pack_type:full_funnel")
    elif "launch_gtm" in pack_key:
        tags.append("pack_type:launch_gtm")
    elif "turnaround" in pack_key:
        tags.append("pack_type:turnaround")
    elif "retention" in pack_key:
        tags.append("pack_type:retention")
    elif "audit" in pack_key or "revamp" in pack_key:
        tags.append("pack_type:audit")
    
    log_event(event_type, project_id=project_id, details=details, tags=tags)


def log_section_generation(
    section_name: str,
    pack_key: str,
    project_id: Optional[str] = None,
    success: bool = True,
    duration_seconds: Optional[float] = None,
    word_count: Optional[int] = None,
    error: Optional[str] = None
) -> None:
    """
    Log individual section generation within a pack.
    
    Args:
        section_name: Name of the section (e.g., "messaging_framework", "content_calendar")
        pack_key: Pack identifier
        project_id: Optional project identifier
        success: Whether generation succeeded
        duration_seconds: Optional generation duration
        word_count: Optional output word count
        error: Optional error message if failed
    """
    output_data = {
        "section": section_name,
        "success": success
    }
    
    if duration_seconds is not None:
        output_data["duration_seconds"] = duration_seconds
    if word_count is not None:
        output_data["word_count"] = word_count
    if error:
        output_data["error"] = error
    
    log_pack_event(
        "SECTION_GENERATED" if success else "SECTION_FAILED",
        pack_key=pack_key,
        project_id=project_id,
        output_data=output_data,
        meta={"section_name": section_name}
    )


def log_pack_quality_assessment(
    pack_key: str,
    project_id: Optional[str] = None,
    quality_score: Optional[float] = None,
    issues: Optional[List[str]] = None,
    passed: bool = True
) -> None:
    """
    Log quality gate assessment for pack output.
    
    Args:
        pack_key: Pack identifier
        project_id: Optional project identifier
        quality_score: Optional numeric quality score (0-100)
        issues: Optional list of quality issues found
        passed: Whether quality gate passed
    """
    output_data = {
        "passed": passed
    }
    
    if quality_score is not None:
        output_data["quality_score"] = quality_score
    if issues:
        output_data["issues"] = issues
        output_data["issues_count"] = len(issues)
    
    log_pack_event(
        "PACK_QUALITY_ASSESSED",
        pack_key=pack_key,
        project_id=project_id,
        output_data=output_data
    )
