"""
CAM Simulation Engine — Phase 10

Enables campaigns to run in SIMULATION mode where:
1. No real emails are sent
2. All state transitions and timing logic still runs
3. Simulated outreach events are recorded for analysis

This allows safe testing before going LIVE.
"""

import logging
from datetime import datetime
from typing import Optional

from aicmo.cam.domain import CampaignMode
from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB

logger = logging.getLogger(__name__)


class SimulatedOutreachEvent:
    """
    Record of a simulated outreach that would have been sent in LIVE mode.
    
    Used for dry-run analysis and planning before going live.
    """
    
    def __init__(
        self,
        campaign_id: int,
        lead_id: int,
        subject: str,
        body_preview: str,
        step_number: int,
        scheduled_time: datetime,
        would_send_at: datetime,
    ):
        self.campaign_id = campaign_id
        self.lead_id = lead_id
        self.subject = subject
        self.body_preview = body_preview  # First 200 chars
        self.step_number = step_number
        self.scheduled_time = scheduled_time
        self.would_send_at = would_send_at
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "campaign_id": self.campaign_id,
            "lead_id": self.lead_id,
            "subject": self.subject,
            "body_preview": self.body_preview,
            "step_number": self.step_number,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "would_send_at": self.would_send_at.isoformat() if self.would_send_at else None,
        }


def should_simulate_outreach(campaign: CampaignDB) -> bool:
    """
    Check if campaign is in SIMULATION mode.
    
    Args:
        campaign: Campaign to check
        
    Returns:
        True if campaign.mode == SIMULATION, False otherwise
    """
    if not campaign:
        return False
    return campaign.mode == CampaignMode.SIMULATION


def record_simulated_outreach(
    campaign: CampaignDB,
    lead: LeadDB,
    subject: str,
    body: str,
    step_number: int,
    scheduled_time: datetime,
    db_session,
) -> Optional[SimulatedOutreachEvent]:
    """
    Record a simulated outreach event (for SIMULATION mode).
    
    Instead of calling EmailSenderPort, this records the event for review.
    
    Args:
        campaign: Campaign in SIMULATION mode
        lead: Lead to simulate sending to
        subject: Email subject
        body: Email body
        step_number: Which step in the sequence
        scheduled_time: When this was scheduled
        db_session: Database session
        
    Returns:
        SimulatedOutreachEvent for analysis, or None if error
    """
    if not should_simulate_outreach(campaign):
        logger.warning(f"record_simulated_outreach called on LIVE campaign {campaign.id}")
        return None
    
    try:
        # Create simulated event
        body_preview = body[:200] + ("..." if len(body) > 200 else "")
        event = SimulatedOutreachEvent(
            campaign_id=campaign.id,
            lead_id=lead.id,
            subject=subject,
            body_preview=body_preview,
            step_number=step_number,
            scheduled_time=scheduled_time,
            would_send_at=datetime.utcnow(),
        )
        
        # Store in OutreachAttemptDB with a marker
        attempt = OutreachAttemptDB(
            lead_id=lead.id,
            campaign_id=campaign.id,
            channel="email",  # or from context
            step_number=step_number,
            status="SIMULATED",  # Custom status to mark as simulated
            last_error=f"[SIMULATION MODE] Would send: {subject}",
        )
        db_session.add(attempt)
        db_session.commit()
        
        logger.info(
            f"[SIMULATION] Campaign {campaign.id}: "
            f"Would send to lead {lead.id}: {subject}"
        )
        
        return event
    
    except Exception as e:
        logger.error(f"Error recording simulated outreach: {e}")
        return None


def get_simulation_summary(
    campaign: CampaignDB,
    db_session,
) -> dict:
    """
    Get summary of simulated outreach events for a campaign.
    
    Args:
        campaign: Campaign to analyze
        db_session: Database session
        
    Returns:
        Summary dict with stats about simulated outreach
    """
    if not should_simulate_outreach(campaign):
        logger.warning(f"get_simulation_summary called on LIVE campaign {campaign.id}")
        return {}
    
    try:
        # Query all OutreachAttemptDB records with status="SIMULATED" for this campaign
        simulated_attempts = db_session.query(OutreachAttemptDB).filter(
            OutreachAttemptDB.campaign_id == campaign.id,
            OutreachAttemptDB.status == "SIMULATED",
        ).all()
        
        # Group by lead
        by_lead = {}
        for attempt in simulated_attempts:
            lead_id = attempt.lead_id
            if lead_id not in by_lead:
                by_lead[lead_id] = []
            by_lead[lead_id].append(attempt)
        
        return {
            "campaign_id": campaign.id,
            "campaign_name": campaign.name,
            "mode": campaign.mode,
            "total_simulated": len(simulated_attempts),
            "unique_leads": len(by_lead),
            "by_lead": {
                lead_id: len(attempts)
                for lead_id, attempts in by_lead.items()
            }
        }
    
    except Exception as e:
        logger.error(f"Error generating simulation summary: {e}")
        return {}


def switch_campaign_mode(
    campaign_id: int,
    new_mode: CampaignMode,
    db_session,
) -> Optional[CampaignDB]:
    """
    Switch a campaign between SIMULATION and LIVE modes.
    
    Args:
        campaign_id: Campaign to switch
        new_mode: New mode (SIMULATION or LIVE)
        db_session: Database session
        
    Returns:
        Updated campaign, or None if not found
    """
    try:
        campaign = db_session.query(CampaignDB).filter(
            CampaignDB.id == campaign_id
        ).first()
        
        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found")
            return None
        
        old_mode = campaign.mode
        campaign.mode = new_mode
        db_session.add(campaign)
        db_session.commit()
        
        logger.info(
            f"Switched campaign {campaign_id} from {old_mode} to {new_mode}"
        )
        
        return campaign
    
    except Exception as e:
        logger.error(f"Error switching campaign mode: {e}")
        return None
