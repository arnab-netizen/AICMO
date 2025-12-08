"""
CAM (Client Acquisition Mode) API Router.

FastAPI endpoints for Phases 7-9:
- Phase 7: Lead Discovery
- Phase 8: Pipeline & Appointments
- Phase 9: Safety & Compliance
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import get_db
from aicmo.cam.discovery import (
    create_discovery_job,
    run_discovery_job,
    convert_profiles_to_leads,
    list_discovery_jobs,
    list_discovered_profiles,
)
from aicmo.cam.discovery_domain import DiscoveryCriteria
from backend.schemas_cam import (
    CamDiscoveryJobCreate,
    CamDiscoveryJobOut,
    CamDiscoveredProfileOut,
    CamConvertProfilesRequest,
    CamConvertProfilesResponse,
    CamLeadStageUpdateRequest,
    CamContactEventIn,
    CamContactEventOut,
    CamAppointmentIn,
    CamAppointmentOut,
)


router = APIRouter(prefix="/api/cam", tags=["cam"])


# ==========================================
# PHASE 7: DISCOVERY ENDPOINTS
# ==========================================

@router.post("/discovery/jobs", response_model=CamDiscoveryJobOut, status_code=201)
def create_discovery_job_endpoint(
    request: CamDiscoveryJobCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new lead discovery job.
    
    Args:
        request: Job creation parameters (name, campaign_id, criteria)
        db: Database session
        
    Returns:
        Created discovery job
    """
    criteria = DiscoveryCriteria(**request.criteria.model_dump())
    
    job_db = create_discovery_job(
        db=db,
        campaign_id=request.campaign_id,
        name=request.name,
        criteria=criteria,
    )
    
    return job_db


@router.post("/discovery/jobs/{job_id}/run", response_model=dict)
def run_discovery_job_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Execute a discovery job.
    
    Runs the job asynchronously and searches configured platforms.
    
    Args:
        job_id: Discovery job ID
        db: Database session
        
    Returns:
        Status message
        
    Raises:
        HTTPException: If job not found or already completed
    """
    try:
        profiles = run_discovery_job(db=db, job_id=job_id)
        return {
            "message": f"Discovery job {job_id} completed",
            "profiles_found": len(profiles),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job execution failed: {str(e)}")


@router.get("/discovery/jobs", response_model=List[CamDiscoveryJobOut])
def list_discovery_jobs_endpoint(
    campaign_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List discovery jobs, optionally filtered by campaign.
    
    Args:
        campaign_id: Optional campaign filter
        db: Database session
        
    Returns:
        List of discovery jobs
    """
    jobs = list_discovery_jobs(db=db, campaign_id=campaign_id)
    return jobs


@router.get("/discovery/jobs/{job_id}/profiles", response_model=List[CamDiscoveredProfileOut])
def list_discovered_profiles_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Get discovered profiles for a job.
    
    Args:
        job_id: Discovery job ID
        db: Database session
        
    Returns:
        List of discovered profiles
    """
    profiles = list_discovered_profiles(db=db, job_id=job_id)
    return profiles


@router.post("/discovery/jobs/{job_id}/profiles/convert", response_model=CamConvertProfilesResponse)
def convert_profiles_endpoint(
    job_id: int,
    request: CamConvertProfilesRequest,
    db: Session = Depends(get_db),
):
    """
    Convert selected profiles to CAM leads.
    
    Args:
        job_id: Discovery job ID (for context)
        request: List of profile IDs to convert
        db: Database session
        
    Returns:
        Number of leads created
        
    Raises:
        HTTPException: If job not found
    """
    from aicmo.cam.db_models import DiscoveryJobDB
    
    # Verify job exists and get campaign_id
    job_db = db.get(DiscoveryJobDB, job_id)
    if not job_db:
        raise HTTPException(status_code=404, detail=f"Discovery job {job_id} not found")
    
    if not job_db.campaign_id:
        raise HTTPException(status_code=400, detail="Job has no associated campaign")
    
    leads_created = convert_profiles_to_leads(
        db=db,
        profile_ids=request.profile_ids,
        campaign_id=job_db.campaign_id,
    )
    
    return CamConvertProfilesResponse(
        leads_created=leads_created,
        message=f"Created {leads_created} new leads from {len(request.profile_ids)} selected profiles",
    )


# ==========================================
# PHASE 8: PIPELINE ENDPOINTS
# ==========================================

@router.get("/pipeline")
def get_pipeline_summary_endpoint(
    campaign_id: int,
    db: Session = Depends(get_db),
):
    """
    Get pipeline summary for a campaign.
    
    Returns counts and sample leads for each stage.
    
    Args:
        campaign_id: Campaign ID to summarize
        db: Database session
        
    Returns:
        Pipeline summary with counts and samples per stage
    """
    from aicmo.cam.pipeline import list_pipeline
    
    try:
        summary = list_pipeline(db=db, campaign_id=campaign_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leads/{lead_id}/stage")
def update_lead_stage_endpoint(
    lead_id: int,
    request: CamLeadStageUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update lead stage.
    
    Args:
        lead_id: Lead ID to update
        request: New stage value
        db: Database session
        
    Returns:
        Success message
    """
    from aicmo.cam.pipeline import update_lead_stage
    
    try:
        lead_db = update_lead_stage(db=db, lead_id=lead_id, stage=request.stage)
        return {
            "lead_id": lead_db.id,
            "stage": lead_db.stage,
            "message": f"Lead stage updated to {lead_db.stage}",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/leads/{lead_id}/events")
def log_contact_event_endpoint(
    lead_id: int,
    request: CamContactEventIn,
    db: Session = Depends(get_db),
):
    """
    Log a contact event for a lead.
    
    Args:
        lead_id: Lead ID to log event for
        request: Event details (channel, direction, summary)
        db: Database session
        
    Returns:
        Created contact event
    """
    from aicmo.cam.pipeline import log_contact_event
    from backend.schemas_cam import CamContactEventOut
    
    try:
        event_db = log_contact_event(
            db=db,
            lead_id=lead_id,
            channel=request.channel,
            direction=request.direction,
            summary=request.summary,
        )
        return CamContactEventOut.model_validate(event_db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/appointments", response_model=List[CamAppointmentOut])
def list_appointments_endpoint(
    campaign_id: Optional[int] = None,
    only_upcoming: bool = True,
    db: Session = Depends(get_db),
):
    """
    List appointments, optionally filtered by campaign.
    
    Args:
        campaign_id: Campaign ID to filter by (optional)
        only_upcoming: If True, only return future appointments
        db: Database session
        
    Returns:
        List of appointments
    """
    from aicmo.cam.pipeline import list_appointments as list_appointments_service
    from backend.schemas_cam import CamAppointmentOut
    
    appointments = list_appointments_service(
        db=db,
        campaign_id=campaign_id,
        only_upcoming=only_upcoming,
    )
    
    return [CamAppointmentOut.model_validate(appt) for appt in appointments]


@router.post("/appointments", response_model=CamAppointmentOut, status_code=201)
def create_appointment_endpoint(
    request: CamAppointmentIn,
    db: Session = Depends(get_db),
):
    """
    Create a new appointment.
    
    Args:
        request: Appointment details (lead_id, scheduled_for, etc.)
        db: Database session
        
    Returns:
        Created appointment
    """
    from aicmo.cam.pipeline import create_appointment
    from backend.schemas_cam import CamAppointmentOut
    
    try:
        appt_db = create_appointment(
            db=db,
            lead_id=request.lead_id,
            scheduled_for=request.scheduled_for,
            duration_minutes=request.duration_minutes,
            location=request.location,
            calendar_link=request.calendar_link,
            notes=request.notes,
        )
        return CamAppointmentOut.model_validate(appt_db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# PHASE 9: SAFETY ENDPOINTS
# ==========================================

@router.get("/safety")
def get_safety_settings_endpoint(
    db: Session = Depends(get_db),
):
    """
    Get current safety and compliance settings.
    
    Returns current rate limits, send windows, and DNC lists.
    
    Args:
        db: Database session
        
    Returns:
        Current safety settings
    """
    from aicmo.cam.safety import get_safety_settings
    from datetime import date, datetime
    
    settings = get_safety_settings(db)
    
    # Convert time objects to HH:MM strings for JSON
    response_data = {
        "per_channel_limits": {
            ch: {
                "channel": cfg.channel,
                "max_per_day": cfg.max_per_day,
                "warmup_enabled": cfg.warmup_enabled,
                "warmup_start": cfg.warmup_start,
                "warmup_increment": cfg.warmup_increment,
                "warmup_max": cfg.warmup_max,
            }
            for ch, cfg in settings.per_channel_limits.items()
        },
        "send_window_start": settings.send_window_start.strftime("%H:%M") if settings.send_window_start else None,
        "send_window_end": settings.send_window_end.strftime("%H:%M") if settings.send_window_end else None,
        "blocked_domains": settings.blocked_domains,
        "do_not_contact_emails": settings.do_not_contact_emails,
        "do_not_contact_lead_ids": settings.do_not_contact_lead_ids,
    }
    
    return response_data


@router.put("/safety")
def update_safety_settings_endpoint(
    request: dict,
    db: Session = Depends(get_db),
):
    """
    Update safety and compliance settings.
    
    Args:
        request: Updated safety settings
        db: Database session
        
    Returns:
        Updated safety settings
    """
    from aicmo.cam.safety import save_safety_settings, SafetySettings, ChannelLimitConfig
    from datetime import time as dt_time
    
    # Convert HH:MM strings to time objects
    send_window_start = None
    send_window_end = None
    
    if request.get("send_window_start"):
        h, m = map(int, request["send_window_start"].split(":"))
        send_window_start = dt_time(h, m)
    
    if request.get("send_window_end"):
        h, m = map(int, request["send_window_end"].split(":"))
        send_window_end = dt_time(h, m)
    
    # Build per_channel_limits
    per_channel_limits = {}
    for ch, cfg_dict in request.get("per_channel_limits", {}).items():
        per_channel_limits[ch] = ChannelLimitConfig(**cfg_dict)
    
    # Create SafetySettings object
    settings = SafetySettings(
        per_channel_limits=per_channel_limits,
        send_window_start=send_window_start,
        send_window_end=send_window_end,
        blocked_domains=request.get("blocked_domains", []),
        do_not_contact_emails=request.get("do_not_contact_emails", []),
        do_not_contact_lead_ids=request.get("do_not_contact_lead_ids", []),
    )
    
    # Save
    saved_settings = save_safety_settings(db, settings)
    
    # Return same format as GET
    response_data = {
        "per_channel_limits": {
            ch: {
                "channel": cfg.channel,
                "max_per_day": cfg.max_per_day,
                "warmup_enabled": cfg.warmup_enabled,
                "warmup_start": cfg.warmup_start,
                "warmup_increment": cfg.warmup_increment,
                "warmup_max": cfg.warmup_max,
            }
            for ch, cfg in saved_settings.per_channel_limits.items()
        },
        "send_window_start": saved_settings.send_window_start.strftime("%H:%M") if saved_settings.send_window_start else None,
        "send_window_end": saved_settings.send_window_end.strftime("%H:%M") if saved_settings.send_window_end else None,
        "blocked_domains": saved_settings.blocked_domains,
        "do_not_contact_emails": saved_settings.do_not_contact_emails,
        "do_not_contact_lead_ids": saved_settings.do_not_contact_lead_ids,
    }
    
    return response_data

