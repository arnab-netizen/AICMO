"""
CAM Pipeline & Appointments (Phase 8).

Domain models and service functions for lead stages, contact events, and appointments.
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_

from aicmo.cam.domain import Channel
from aicmo.cam.db_models import LeadDB, ContactEventDB, AppointmentDB


class LeadStage(str, Enum):
    """Lead progression stages in the pipeline."""
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    REPLIED = "REPLIED"
    QUALIFIED = "QUALIFIED"
    WON = "WON"
    LOST = "LOST"


class ContactEvent(BaseModel):
    """Contact interaction event (reply, call, meeting)."""
    id: Optional[int] = None
    lead_id: int
    channel: Channel
    direction: str  # "OUTBOUND" / "INBOUND"
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Appointment(BaseModel):
    """Scheduled appointment with a lead."""
    id: Optional[int] = None
    lead_id: int
    scheduled_for: datetime
    duration_minutes: int = 30
    location: Optional[str] = None  # "Zoom", "Google Meet", "Phone", etc.
    calendar_link: Optional[str] = None
    notes: Optional[str] = None
    status: str = "SCHEDULED"  # "SCHEDULED", "COMPLETED", "CANCELLED"


# ==========================================
# SERVICE FUNCTIONS
# ==========================================

def update_lead_stage(db: Session, lead_id: int, stage: LeadStage) -> LeadDB:
    """
    Update a lead's pipeline stage.
    
    Args:
        db: Database session
        lead_id: Lead ID
        stage: New stage (LeadStage enum or string)
        
    Returns:
        Updated lead
        
    Raises:
        ValueError: If lead not found
    """
    lead = db.get(LeadDB, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    # Handle stage as either LeadStage enum or string
    stage_str = stage.value if isinstance(stage, LeadStage) else stage
    lead.stage = stage_str
    db.commit()
    db.refresh(lead)
    return lead


def log_contact_event(
    db: Session,
    lead_id: int,
    channel: Channel,
    direction: str,
    summary: str
) -> ContactEventDB:
    """
    Log a contact interaction event.
    
    Args:
        db: Database session
        lead_id: Lead ID
        channel: Communication channel
        direction: "OUTBOUND" or "INBOUND"
        summary: Event description
        
    Returns:
        Created contact event
        
    Raises:
        ValueError: If lead not found
    """
    # Verify lead exists
    lead = db.get(LeadDB, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    # Handle channel as either Channel enum or string
    channel_str = channel.value if isinstance(channel, Channel) else channel
    
    event = ContactEventDB(
        lead_id=lead_id,
        channel=channel_str,
        direction=direction,
        summary=summary,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_appointment(
    db: Session,
    lead_id: int,
    scheduled_for: datetime,
    duration_minutes: int = 30,
    location: Optional[str] = None,
    calendar_link: Optional[str] = None,
    notes: Optional[str] = None
) -> AppointmentDB:
    """
    Create an appointment with a lead.
    
    Args:
        db: Database session
        lead_id: Lead ID
        scheduled_for: Appointment date/time
        duration_minutes: Duration in minutes
        location: Meeting location/platform
        calendar_link: Calendar invitation link
        notes: Additional notes
        
    Returns:
        Created appointment
        
    Raises:
        ValueError: If lead not found
    """
    # Verify lead exists
    lead = db.get(LeadDB, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    appointment = AppointmentDB(
        lead_id=lead_id,
        scheduled_for=scheduled_for,
        duration_minutes=duration_minutes,
        location=location,
        calendar_link=calendar_link,
        notes=notes,
        status="SCHEDULED",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def list_pipeline(db: Session, campaign_id: int) -> dict:
    """
    Get pipeline summary for a campaign.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        
    Returns:
        Dictionary with campaign_id, individual stage counts, and sample_leads
    """
    # Get all leads for the campaign
    leads = db.query(LeadDB).filter(LeadDB.campaign_id == campaign_id).all()
    
    # Build result with campaign_id and counts
    result = {"campaign_id": campaign_id}
    sample_leads = {}
    
    for stage in LeadStage:
        stage_leads = [l for l in leads if l.stage == stage.value]
        
        # Add count with key like "new_count", "contacted_count"
        count_key = f"{stage.value.lower()}_count"
        result[count_key] = len(stage_leads)
        
        # Include up to 5 sample leads per stage
        sample_leads[stage.value] = [
            {
                "id": lead.id,
                "name": lead.name,
                "company": lead.company,
                "role": lead.role,
                "stage": lead.stage,
            }
            for lead in stage_leads[:5]
        ]
    
    result["sample_leads"] = sample_leads
    return result


def list_appointments(
    db: Session,
    campaign_id: int,
    only_upcoming: bool = True
) -> List[AppointmentDB]:
    """
    List appointments for a campaign.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        only_upcoming: If True, only show future appointments
        
    Returns:
        List of appointments
    """
    # Get lead IDs for the campaign
    lead_ids = [lead.id for lead in db.query(LeadDB).filter(LeadDB.campaign_id == campaign_id).all()]
    
    if not lead_ids:
        return []
    
    query = db.query(AppointmentDB).filter(AppointmentDB.lead_id.in_(lead_ids))
    
    if only_upcoming:
        query = query.filter(AppointmentDB.scheduled_for >= datetime.utcnow())
    
    return query.order_by(AppointmentDB.scheduled_for).all()
