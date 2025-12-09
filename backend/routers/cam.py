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


# ==========================================
# PHASE 4-5: AUTONOMOUS ENGINE ENDPOINTS
# ==========================================


@router.get("/campaigns", response_model=List[dict])
def list_campaigns(db: Session = Depends(get_db)):
    """
    List all campaigns with their current metrics.
    
    Returns:
        List of campaigns with lead counts and status
    """
    from aicmo.cam.db_models import CampaignDB
    from aicmo.cam.engine.targets_tracker import compute_campaign_metrics
    
    campaigns = db.query(CampaignDB).all()
    
    result = []
    for campaign in campaigns:
        metrics = compute_campaign_metrics(db, campaign.id)
        result.append({
            "id": campaign.id,
            "name": campaign.name,
            "active": campaign.active,
            "target_niche": campaign.target_niche,
            "service_key": campaign.service_key,
            "target_clients": campaign.target_clients,
            "current_leads": metrics.total_leads,
            "qualified_leads": metrics.status_qualified,
            "conversion_rate": metrics.conversion_rate,
            "goal_progress": metrics.qualified_pct,
        })
    
    return result


@router.get("/campaigns/{campaign_id}", response_model=dict)
def get_campaign_details(campaign_id: int, db: Session = Depends(get_db)):
    """
    Get detailed metrics for a campaign.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        
    Returns:
        Campaign details with full metrics breakdown
        
    Raises:
        HTTPException: If campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    from aicmo.cam.engine.targets_tracker import compute_campaign_metrics
    from aicmo.cam.engine.outreach_engine import get_outreach_stats
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    metrics = compute_campaign_metrics(db, campaign_id)
    outreach_stats = get_outreach_stats(db, campaign_id, days=1)
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "active": campaign.active,
        "description": campaign.description,
        "target_niche": campaign.target_niche,
        "service_key": campaign.service_key,
        "target_clients": campaign.target_clients,
        "target_mrr": campaign.target_mrr,
        "channels_enabled": campaign.channels_enabled,
        "max_emails_per_day": campaign.max_emails_per_day,
        "metrics": {
            "total_leads": metrics.total_leads,
            "leads_by_status": {
                "new": metrics.status_new,
                "enriched": metrics.status_enriched,
                "contacted": metrics.status_contacted,
                "replied": metrics.status_replied,
                "qualified": metrics.status_qualified,
                "lost": metrics.status_lost,
            },
            "conversion_rate": metrics.conversion_rate,
            "goal_progress": metrics.qualified_pct,
        },
        "today_outreach": {
            "total": outreach_stats["total"],
            "sent": outreach_stats["sent"],
            "failed": outreach_stats["failed"],
            "skipped": outreach_stats["skipped"],
        },
    }


@router.post("/campaigns", response_model=dict, status_code=201)
def create_campaign(request: dict, db: Session = Depends(get_db)):
    """
    Create a new CAM campaign.
    
    Args:
        request: Campaign creation data (name, target_niche, service_key, target_clients, etc.)
        db: Database session
        
    Returns:
        Created campaign
        
    Raises:
        HTTPException: If campaign name already exists
    """
    from aicmo.cam.db_models import CampaignDB
    
    name = request.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Campaign name required")
    
    # Check for duplicate
    existing = db.query(CampaignDB).filter(CampaignDB.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Campaign '{name}' already exists")
    
    campaign = CampaignDB(
        name=name,
        description=request.get("description"),
        target_niche=request.get("target_niche"),
        service_key=request.get("service_key"),
        target_clients=request.get("target_clients"),
        target_mrr=request.get("target_mrr"),
        channels_enabled=request.get("channels_enabled", ["email"]),
        max_emails_per_day=request.get("max_emails_per_day", 20),
        max_outreach_per_day=request.get("max_outreach_per_day", 50),
        active=True,
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "active": campaign.active,
        "message": f"Campaign '{name}' created successfully",
    }


@router.put("/campaigns/{campaign_id}/pause", response_model=dict)
def pause_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Pause a campaign (stop all outreach).
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        
    Returns:
        Confirmation
        
    Raises:
        HTTPException: If campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    campaign.active = False
    db.commit()
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "active": campaign.active,
        "message": f"Campaign '{campaign.name}' paused",
    }


@router.put("/campaigns/{campaign_id}/resume", response_model=dict)
def resume_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """
    Resume a paused campaign.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        
    Returns:
        Confirmation
        
    Raises:
        HTTPException: If campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    campaign.active = True
    db.commit()
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "active": campaign.active,
        "message": f"Campaign '{campaign.name}' resumed",
    }


@router.post("/campaigns/{campaign_id}/run-cycle", response_model=dict)
def run_campaign_cycle(
    campaign_id: int,
    dry_run: bool = True,
    db: Session = Depends(get_db),
):
    """
    Manually trigger CAM cycle for a campaign.
    
    Runs lead discovery, enrichment, and outreach in sequence.
    
    Args:
        campaign_id: Campaign ID
        dry_run: If True, don't send real emails (default: True)
        db: Database session
        
    Returns:
        Execution statistics
        
    Raises:
        HTTPException: If campaign not found
    """
    from aicmo.cam.auto_runner import run_cam_cycle_for_campaign
    
    stats = run_cam_cycle_for_campaign(db, campaign_id, dry_run=dry_run)
    
    if "error" in stats:
        raise HTTPException(status_code=400, detail=stats["error"])
    
    return {
        "campaign_id": campaign_id,
        "dry_run": dry_run,
        "leads_discovered": stats.get("leads_discovered", 0),
        "leads_enriched": stats.get("leads_enriched", 0),
        "outreach_sent": stats.get("outreach_sent", 0),
        "outreach_failed": stats.get("outreach_failed", 0),
        "outreach_skipped": stats.get("outreach_skipped", 0),
        "errors": stats.get("errors", []),
    }

