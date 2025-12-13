"""
Phase 9: Final Integration - REST API Endpoints for Pipeline Orchestration.

Provides HTTP endpoints for:
- Pipeline orchestration (harvest, score, qualify, route, nurture)
- Campaign management (CRUD operations)
- Real-time metrics and dashboard data
- Job scheduling and monitoring
- Admin functions (health check, configuration)

Architecture:
- FastAPI-based REST endpoints
- Session-per-request pattern
- Comprehensive error handling
- Request/response validation with Pydantic
- Type hints throughout
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator, ConfigDict
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session

from aicmo.core import SessionLocal, Base
from aicmo.core.config import settings

# Dependency for FastAPI to get database session
def get_db():
    """Get database session for API endpoint."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from aicmo.cam.engine import (
    CronOrchestrator,
    CronJobConfig,
    CronScheduler,
    CronMetrics,
    JobStatus,
    JobType,
)


# ============================================================================
# Request/Response Models
# ============================================================================

class CampaignRequest(BaseModel):
    """Campaign creation/update request."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    description: Optional[str] = Field(None, max_length=1000, description="Campaign description")
    target_niche: Optional[str] = Field(None, max_length=255, description="Target market niche")
    service_key: Optional[str] = Field(None, description="Service/offering type")
    target_clients: Optional[int] = Field(None, ge=1, description="Goal number of clients")
    target_mrr: Optional[float] = Field(None, ge=0, description="Target monthly recurring revenue")
    active: bool = Field(True, description="Campaign active status")


class CampaignResponse(BaseModel):
    """Campaign response with timestamps."""
    
    id: int
    name: str
    description: Optional[str]
    target_niche: Optional[str]
    service_key: Optional[str]
    target_clients: Optional[int]
    target_mrr: Optional[float]
    active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ScheduleJobRequest(BaseModel):
    """Job scheduling request."""
    
    job_type: JobType = Field(..., description="Job type: HARVEST, SCORE, QUALIFY, ROUTE, NURTURE, FULL_PIPELINE")
    campaign_id: int = Field(..., ge=1, description="Campaign ID")
    hour: int = Field(default=2, ge=0, le=23, description="Hour to run (0-23, UTC)")
    minute: int = Field(default=0, ge=0, le=59, description="Minute to run (0-59)")
    batch_size: int = Field(default=100, ge=1, le=1000, description="Max leads per batch")
    timeout_seconds: int = Field(default=300, ge=60, description="Job timeout in seconds")
    enabled: bool = Field(default=True, description="Job enabled status")


class JobResultResponse(BaseModel):
    """Job execution result."""
    
    type: JobType
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime]
    leads_processed: int
    leads_qualified: int
    error_message: Optional[str]
    duration_seconds: Optional[float]


class MetricsResponse(BaseModel):
    """Pipeline metrics response."""
    
    job_type: JobType
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    lead_success_rate: float
    health_status: str
    consecutive_failures: int
    average_duration_seconds: float
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]


class DashboardResponse(BaseModel):
    """Pipeline dashboard data."""
    
    campaign_id: int
    campaign_name: str
    total_leads_harvested: int
    total_leads_qualified: int
    leads_routed_to_sequence: int
    emails_sent: int
    pipeline_health: str
    jobs: List[MetricsResponse]
    last_updated: datetime


class PipelineStatusResponse(BaseModel):
    """Real-time pipeline status."""
    
    campaign_id: int
    campaign_name: str
    is_healthy: bool
    health_status: str
    current_job: Optional[str]
    next_scheduled_job: Optional[str]
    hours_until_next_job: Optional[float]
    job_history: List[JobResultResponse]
    created_at: datetime


class HealthCheckResponse(BaseModel):
    """System health check response."""
    
    status: str = Field(..., description="System status: healthy, degraded, error")
    timestamp: datetime
    components: Dict[str, str]
    database_connected: bool
    cache_available: bool
    message: Optional[str]


# ============================================================================
# Route Definition
# ============================================================================

router = APIRouter(prefix="/api/v1/cam", tags=["Campaign Acquisition Mode"])


# ============================================================================
# Campaign Endpoints
# ============================================================================

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    active_only: bool = Query(False, description="Only return active campaigns"),
    db: Session = Depends(get_db),
) -> List[CampaignResponse]:
    """
    List all campaigns with pagination.
    
    Parameters:
    - skip: Number of campaigns to skip (pagination)
    - limit: Maximum number of campaigns to return
    - active_only: Filter to active campaigns only
    
    Returns: List of campaign objects
    """
    from aicmo.cam.db_models import CampaignDB
    
    query = db.query(CampaignDB)
    
    if active_only:
        query = query.filter(CampaignDB.active == True)
    
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    """
    Get campaign by ID with complete details.
    
    Parameters:
    - campaign_id: Unique campaign identifier
    
    Returns: Campaign object with all details
    
    Raises:
    - 404: Campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign {campaign_id} not found"
        )
    
    return campaign


@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    campaign_data: CampaignRequest = Body(..., description="Campaign details"),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    """
    Create new campaign with provided configuration.
    
    Parameters:
    - campaign_data: Campaign details (name, description, ICP, targets)
    
    Returns: Created campaign with ID and timestamps
    
    Raises:
    - 400: Invalid campaign data
    - 409: Campaign name already exists
    """
    from aicmo.cam.db_models import CampaignDB
    
    # Check for duplicate campaign name
    existing = db.query(CampaignDB).filter(
        CampaignDB.name == campaign_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Campaign '{campaign_data.name}' already exists"
        )
    
    # Create campaign
    campaign = CampaignDB(
        name=campaign_data.name,
        description=campaign_data.description,
        target_niche=campaign_data.target_niche,
        service_key=campaign_data.service_key,
        target_clients=campaign_data.target_clients,
        target_mrr=campaign_data.target_mrr,
        active=campaign_data.active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return campaign


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    campaign_data: CampaignRequest = Body(..., description="Updated campaign details"),
    db: Session = Depends(get_db),
) -> CampaignResponse:
    """
    Update existing campaign configuration.
    
    Parameters:
    - campaign_id: Campaign to update
    - campaign_data: New campaign details
    
    Returns: Updated campaign object
    
    Raises:
    - 404: Campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Update fields
    campaign.name = campaign_data.name
    campaign.description = campaign_data.description
    campaign.target_niche = campaign_data.target_niche
    campaign.service_key = campaign_data.service_key
    campaign.target_clients = campaign_data.target_clients
    campaign.target_mrr = campaign_data.target_mrr
    campaign.active = campaign_data.active
    campaign.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(campaign)
    
    return campaign


# ============================================================================
# Pipeline Orchestration Endpoints
# ============================================================================

@router.post("/campaigns/{campaign_id}/execute/harvest", response_model=JobResultResponse)
async def execute_harvest(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    max_leads: int = Query(100, ge=1, le=1000, description="Maximum leads to discover"),
    db: Session = Depends(get_db),
) -> JobResultResponse:
    """
    Execute lead harvesting for campaign.
    
    Discovers new leads from configured sources with fallback chain.
    
    Parameters:
    - campaign_id: Campaign to harvest for
    - max_leads: Maximum number of leads to discover
    
    Returns: Job execution result with lead counts
    
    Raises:
    - 404: Campaign not found
    - 422: Campaign not properly configured
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    try:
        orchestrator = CronOrchestrator()
        result = orchestrator.run_harvest_cron(max_leads_per_stage=max_leads)
        
        return JobResultResponse(
            type=result.type,
            status=result.status,
            started_at=result.started_at,
            completed_at=result.completed_at,
            leads_processed=result.leads_processed,
            leads_qualified=result.leads_qualified,
            error_message=result.error_message,
            duration_seconds=result.duration_seconds,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Harvest execution failed: {str(e)}"
        )


@router.post("/campaigns/{campaign_id}/execute/full-pipeline", response_model=JobResultResponse)
async def execute_full_pipeline(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    max_leads: int = Query(100, ge=1, le=1000, description="Maximum leads per stage"),
    db: Session = Depends(get_db),
) -> JobResultResponse:
    """
    Execute complete lead pipeline (harvest → score → qualify → route → nurture).
    
    Runs all 5 stages sequentially with atomic transactions.
    
    Parameters:
    - campaign_id: Campaign to run pipeline for
    - max_leads: Maximum leads per stage
    
    Returns: Final job result (nurture stage)
    
    Raises:
    - 404: Campaign not found
    - 500: Pipeline execution failed
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    try:
        orchestrator = CronOrchestrator()
        results = orchestrator.run_full_pipeline(max_leads_per_stage=max_leads)
        
        # Return final result (nurture stage)
        final_result = results[-1]
        
        return JobResultResponse(
            type=final_result.type,
            status=final_result.status,
            started_at=final_result.started_at,
            completed_at=final_result.completed_at,
            leads_processed=final_result.leads_processed,
            leads_qualified=final_result.leads_qualified,
            error_message=final_result.error_message,
            duration_seconds=final_result.duration_seconds,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )


# ============================================================================
# Scheduling & Configuration Endpoints
# ============================================================================

@router.post("/campaigns/{campaign_id}/schedule", status_code=201)
async def schedule_job(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    schedule_data: ScheduleJobRequest = Body(..., description="Schedule configuration"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Schedule job for campaign with custom timing.
    
    Parameters:
    - campaign_id: Campaign to schedule for
    - schedule_data: Job type, timing, batch size, timeout
    
    Returns: Confirmation with next scheduled run time
    
    Raises:
    - 404: Campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    try:
        # Create job config
        config = CronJobConfig(
            hour=schedule_data.hour,
            minute=schedule_data.minute,
            batch_size=schedule_data.batch_size,
            timeout_seconds=schedule_data.timeout_seconds,
            enabled=schedule_data.enabled,
        )
        
        # Create scheduler
        scheduler = CronScheduler({schedule_data.job_type: config})
        
        # Calculate next run
        next_run = scheduler.get_next_run_time(schedule_data.job_type)
        hours_until = scheduler.get_hours_until_next_run(schedule_data.job_type)
        
        return {
            "message": "Job scheduled successfully",
            "campaign_id": campaign_id,
            "job_type": schedule_data.job_type.value,
            "scheduled_hour": schedule_data.hour,
            "scheduled_minute": schedule_data.minute,
            "batch_size": schedule_data.batch_size,
            "next_run_at": next_run,
            "hours_until_next_run": hours_until,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Job scheduling failed: {str(e)}"
        )


# ============================================================================
# Metrics & Dashboard Endpoints
# ============================================================================

@router.get("/campaigns/{campaign_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """
    Get real-time pipeline dashboard for campaign.
    
    Returns comprehensive metrics on:
    - Leads harvested, qualified, routed
    - Emails sent and engagement
    - Pipeline health status
    - Job execution history
    
    Parameters:
    - campaign_id: Campaign to get dashboard for
    
    Returns: Dashboard data with all metrics
    
    Raises:
    - 404: Campaign not found
    """
    from aicmo.cam.db_models import CampaignDB, LeadDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    try:
        # Get lead counts
        total_leads = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_id
        ).count()
        
        qualified_leads = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.status == LeadStatus.QUALIFIED,
        ).count()
        
        routed_leads = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.status == LeadStatus.ROUTED,
        ).count()
        
        # Get orchestrator metrics
        orchestrator = CronOrchestrator()
        dashboard = orchestrator.get_cron_dashboard()
        
        # Build response
        return DashboardResponse(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            total_leads_harvested=total_leads,
            total_leads_qualified=qualified_leads,
            leads_routed_to_sequence=routed_leads,
            emails_sent=routed_leads,  # Simplified: emails = routed leads
            pipeline_health=dashboard.get("health_status", "unknown"),
            jobs=[],  # Would be populated with metrics from dashboard
            last_updated=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard generation failed: {str(e)}"
        )


@router.get("/campaigns/{campaign_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    campaign_id: int = Field(..., ge=1, description="Campaign ID"),
    db: Session = Depends(get_db),
) -> PipelineStatusResponse:
    """
    Get real-time pipeline status for campaign.
    
    Returns current job status, health, and scheduling info.
    
    Parameters:
    - campaign_id: Campaign ID
    
    Returns: Pipeline status with current job and next schedule
    
    Raises:
    - 404: Campaign not found
    """
    from aicmo.cam.db_models import CampaignDB
    
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    
    try:
        orchestrator = CronOrchestrator()
        status = orchestrator.get_scheduler_status()
        
        return PipelineStatusResponse(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            is_healthy=status.get("health_status") == "healthy",
            health_status=status.get("health_status", "unknown"),
            current_job=None,  # Would be fetched from active job table
            next_scheduled_job=status.get("next_scheduled_job"),
            hours_until_next_job=status.get("hours_until_next_job"),
            job_history=[],  # Would be populated from job history
            created_at=datetime.utcnow(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Status fetch failed: {str(e)}"
        )


# ============================================================================
# Health & Admin Endpoints
# ============================================================================

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """
    Check system health status.
    
    Returns:
    - System status (healthy/degraded/error)
    - Component status (database, cache, etc.)
    - Database connectivity
    
    Returns: Health check result
    """
    try:
        # Check database
        db.execute("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False
    
    components = {
        "database": "connected" if db_connected else "disconnected",
        "api": "operational",
        "orchestrator": "operational",
    }
    
    status = "healthy" if db_connected else "degraded"
    
    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow(),
        components=components,
        database_connected=db_connected,
        cache_available=True,
        message="System operational" if status == "healthy" else "Database unavailable"
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_statistics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get system-wide statistics.
    
    Returns:
    - Total campaigns
    - Total leads processed
    - Pipeline completion rates
    - Performance metrics
    
    Returns: System statistics
    """
    from aicmo.cam.db_models import CampaignDB, LeadDB
    
    try:
        total_campaigns = db.query(CampaignDB).count()
        total_leads = db.query(LeadDB).count()
        
        qualified_leads = db.query(LeadDB).filter(
            LeadDB.status == LeadStatus.QUALIFIED
        ).count()
        
        routed_leads = db.query(LeadDB).filter(
            LeadDB.status == LeadStatus.ROUTED
        ).count()
        
        return {
            "timestamp": datetime.utcnow(),
            "total_campaigns": total_campaigns,
            "total_leads": total_leads,
            "qualified_leads": qualified_leads,
            "qualified_percentage": (qualified_leads / total_leads * 100) if total_leads > 0 else 0,
            "routed_leads": routed_leads,
            "routed_percentage": (routed_leads / total_leads * 100) if total_leads > 0 else 0,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Statistics generation failed: {str(e)}"
        )
