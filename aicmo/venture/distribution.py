"""
Distribution service with safety enforcement.

MODULE 2: Safe outreach execution.
"""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from aicmo.venture.distribution_models import DistributionJobDB
from aicmo.venture.enforcement import enforce_campaign_safety
from aicmo.venture.lead_capture import is_contactable
from aicmo.cam.db_models import LeadDB


class DistributionBlocked(Exception):
    """Raised when distribution is blocked by safety checks."""
    pass


@dataclass
class DistributionRequest:
    """Request to send a message to a lead."""
    venture_id: str
    campaign_id: int
    lead_id: int
    channel: str
    message_content: str


def can_distribute(session: Session, campaign_id: int, lead_id: int) -> tuple[bool, Optional[str]]:
    """
    Check if distribution is allowed.
    
    Returns:
        (allowed, reason) - True if allowed, False with reason if blocked
    """
    # Check campaign safety
    try:
        enforce_campaign_safety(session, campaign_id)
    except Exception as e:
        return False, str(e)
    
    # Check lead contactability (DNC enforcement)
    if not is_contactable(session, lead_id):
        lead = session.query(LeadDB).filter_by(id=lead_id).first()
        if lead and lead.consent_status == "DNC":
            return False, "Lead is on Do Not Contact list"
        return False, "Lead cannot be contacted"
    
    return True, None


def execute_distribution(
    session: Session,
    request: DistributionRequest,
    dry_run: bool = False
) -> DistributionJobDB:
    """
    Execute distribution with full safety checks.
    
    Args:
        session: Database session
        request: Distribution request
        dry_run: If True, perform checks but don't actually send
        
    Returns:
        DistributionJobDB record
        
    Raises:
        DistributionBlocked: If safety checks fail
    """
    # Safety checks
    allowed, reason = can_distribute(session, request.campaign_id, request.lead_id)
    if not allowed:
        # Create BLOCKED job record
        job = DistributionJobDB(
            venture_id=request.venture_id,
            campaign_id=request.campaign_id,
            lead_id=request.lead_id,
            channel=request.channel,
            status="BLOCKED",
            error=reason,
            created_at=datetime.now(timezone.utc)
        )
        session.add(job)
        session.commit()
        raise DistributionBlocked(reason)
    
    # Create job record
    job = DistributionJobDB(
        venture_id=request.venture_id,
        campaign_id=request.campaign_id,
        lead_id=request.lead_id,
        channel=request.channel,
        status="PENDING" if not dry_run else "DRY_RUN",
        created_at=datetime.now(timezone.utc)
    )
    session.add(job)
    
    if dry_run:
        job.executed_at = datetime.now(timezone.utc)
        session.commit()
        return job
    
    # TODO: Actual sending logic would go here
    # For now, mark as SENT
    job.status = "SENT"
    job.executed_at = datetime.now(timezone.utc)
    job.message_id = f"msg_{job.id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    session.commit()
    return job


def get_distribution_count(
    session: Session,
    campaign_id: int,
    since: Optional[datetime] = None
) -> int:
    """
    Count distributions for rate limiting.
    
    Args:
        session: Database session
        campaign_id: Campaign ID
        since: Count only since this timestamp
        
    Returns:
        Count of distributions
    """
    query = session.query(DistributionJobDB).filter(
        DistributionJobDB.campaign_id == campaign_id,
        DistributionJobDB.status.in_(["SENT", "PENDING"])
    )
    
    if since:
        query = query.filter(DistributionJobDB.created_at >= since)
    
    return query.count()
