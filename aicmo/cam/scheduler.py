"""
CAM scheduler.

Phase CAM-4: Decide who to contact next and record attempts.
"""

from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from aicmo.cam.db_models import LeadDB, OutreachAttemptDB
from aicmo.cam.domain import AttemptStatus, Channel


def find_leads_to_contact(
    db: Session,
    campaign_id: int,
    channel: Channel,
    limit: int = 50,
) -> List[LeadDB]:
    """
    Return leads in a campaign that should be contacted.
    
    Simple initial logic:
    - In the specified campaign
    - Not marked as LOST
    - Ordered by creation date (oldest first)
    
    Args:
        db: Database session
        campaign_id: Campaign ID to filter by
        channel: Channel to contact on
        limit: Maximum number of leads to return
        
    Returns:
        List of LeadDB instances ready for outreach
    """
    q = (
        db.query(LeadDB)
        .filter(LeadDB.campaign_id == campaign_id)
        .order_by(LeadDB.created_at.asc())
        .limit(limit)
    )
    return list(q)


def record_attempt(
    db: Session,
    lead_id: int,
    campaign_id: int,
    channel: Channel,
    step_number: int,
    status: AttemptStatus,
    last_error: str | None = None,
) -> OutreachAttemptDB:
    """
    Record an outreach attempt in the database.
    
    Args:
        db: Database session
        lead_id: Lead ID
        campaign_id: Campaign ID
        channel: Communication channel
        step_number: Sequence step number
        status: Attempt status
        last_error: Error message if failed
        
    Returns:
        Created OutreachAttemptDB instance
    """
    attempt = OutreachAttemptDB(
        lead_id=lead_id,
        campaign_id=campaign_id,
        channel=channel,
        step_number=step_number,
        status=status,
        last_error=last_error,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt
