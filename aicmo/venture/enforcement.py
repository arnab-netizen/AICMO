"""
Venture safety enforcement.

MODULE 0: Ensures campaigns only execute when safe to do so.
"""

from sqlalchemy.orm import Session
from aicmo.venture.models import CampaignConfigDB, CampaignStatus


class SafetyViolation(Exception):
    """Raised when attempting to execute an unsafe campaign operation."""
    pass


def enforce_campaign_safety(session: Session, campaign_id: int) -> CampaignConfigDB:
    """
    Enforce campaign safety checks before any distribution.
    
    BLOCKS execution if:
    - Campaign status is not RUNNING
    - Kill switch is activated
    - Campaign config doesn't exist
    
    Args:
        session: Database session
        campaign_id: ID of campaign to check
        
    Returns:
        CampaignConfigDB if safe to proceed
        
    Raises:
        SafetyViolation: If campaign is not safe to execute
    """
    config = session.query(CampaignConfigDB).filter_by(campaign_id=campaign_id).first()
    
    if not config:
        raise SafetyViolation(f"Campaign {campaign_id} has no configuration")
    
    if config.status != CampaignStatus.RUNNING:
        raise SafetyViolation(
            f"Campaign {campaign_id} is {config.status.value}, must be RUNNING"
        )
    
    if config.kill_switch:
        raise SafetyViolation(
            f"Campaign {campaign_id} kill switch is ACTIVE - all execution blocked"
        )
    
    return config


def can_send_message(session: Session, campaign_id: int) -> bool:
    """
    Quick check if campaign can send messages (non-blocking).
    
    Returns:
        True if safe to send, False otherwise
    """
    try:
        enforce_campaign_safety(session, campaign_id)
        return True
    except SafetyViolation:
        return False
