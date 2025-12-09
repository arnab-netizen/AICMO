"""
CAM Safety Limits — Rate limiting and daily email caps enforcement.

Phase 4: Centralizes safety/rate limits for daily email caps, per-campaign caps,
and tracks quota usage per day.

Uses existing SafetySettings/SafetySettingsDB and Campaign model fields:
- campaign.max_emails_per_day (int, optional)
- campaign.max_outreach_per_day (int, optional)
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, cast, func, Date

from aicmo.cam.db_models import CampaignDB, OutreachAttemptDB, AttemptStatus
from aicmo.cam.domain import Channel


# ═══════════════════════════════════════════════════════════════════════
# QUOTA CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════


def get_daily_email_limit(campaign: CampaignDB) -> int:
    """
    Get the daily email sending limit for a campaign.
    
    Uses campaign.max_emails_per_day if set, otherwise defaults to 20.
    
    Args:
        campaign: Campaign from database
        
    Returns:
        Maximum emails allowed per day for this campaign
    """
    if campaign.max_emails_per_day and campaign.max_emails_per_day > 0:
        return campaign.max_emails_per_day
    # Default conservative limit
    return 20


def remaining_email_quota(
    db: Session,
    campaign_id: int,
    now: datetime,
) -> int:
    """
    Calculate remaining email quota for a campaign today.
    
    Counts emails already sent today via OutreachAttemptDB.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        now: Current datetime (for determining "today")
        
    Returns:
        Number of emails still available to send today (can be negative if over limit)
    """
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        return 0
    
    daily_limit = get_daily_email_limit(campaign)
    
    # Count emails sent today (by channel, regardless of success)
    today = now.date()
    sent_count = (
        db.query(func.count(OutreachAttemptDB.id))
        .filter(
            and_(
                OutreachAttemptDB.campaign_id == campaign_id,
                OutreachAttemptDB.channel == Channel.EMAIL,
                cast(OutreachAttemptDB.created_at, Date) == today,
            )
        )
        .scalar()
    ) or 0
    
    remaining = daily_limit - sent_count
    return max(-100, remaining)  # Cap at -100 for safety


def can_send_email(
    db: Session,
    campaign_id: int,
    now: datetime,
) -> tuple[bool, str]:
    """
    Check if campaign can send an email right now.
    
    Checks:
    1. Campaign is active
    2. Email is in allowed channels
    3. Daily quota not exceeded
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        now: Current datetime
        
    Returns:
        Tuple (can_send: bool, reason: str)
    """
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        return False, "Campaign not found"
    
    if not campaign.active:
        return False, "Campaign is inactive"
    
    # Check if email is enabled
    channels_enabled = campaign.channels_enabled or ["email"]
    if Channel.EMAIL not in channels_enabled:
        return False, "Email channel disabled for this campaign"
    
    # Check quota
    quota = remaining_email_quota(db, campaign_id, now)
    if quota <= 0:
        return False, f"Daily email quota exhausted (limit: {get_daily_email_limit(campaign)})"
    
    return True, "OK"


# ═══════════════════════════════════════════════════════════════════════
# QUOTA TRACKING
# ═══════════════════════════════════════════════════════════════════════


def register_email_sent(
    db: Session,
    campaign_id: int,
    lead_id: int,
    attempt_status: AttemptStatus,
    now: datetime,
) -> None:
    """
    Register an email send attempt in the database.
    
    This updates quota tracking. Called after every email attempt
    (sent, failed, or skipped).
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        lead_id: Lead ID
        attempt_status: Result of the attempt (SENT, FAILED, SKIPPED, etc.)
        now: Current datetime
        
    Returns:
        None (updates database in-place)
    """
    # Note: The actual OutreachAttemptDB insert is usually done by sender.py
    # This function is a convenience for explicit quota registration.
    # For now, it's a no-op since OutreachAttemptDB.created_at is set automatically.
    pass


# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════


def get_today_email_count(
    db: Session,
    campaign_id: int,
    now: datetime,
) -> int:
    """
    Get count of emails sent today for a campaign.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        now: Current datetime
        
    Returns:
        Count of email attempts today
    """
    today = now.date()
    count = (
        db.query(func.count(OutreachAttemptDB.id))
        .filter(
            and_(
                OutreachAttemptDB.campaign_id == campaign_id,
                OutreachAttemptDB.channel == Channel.EMAIL,
                cast(OutreachAttemptDB.created_at, Date) == today,
            )
        )
        .scalar()
    ) or 0
    return count


def reset_daily_quota(db: Session, campaign_id: int, now: datetime) -> None:
    """
    Reset daily quota tracking for a campaign.
    
    This is called at midnight or for manual reset.
    Currently a no-op since we track by date in OutreachAttemptDB.created_at.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        now: Current datetime
        
    Returns:
        None
    """
    # No-op: quotas are tracked by created_at date automatically
    pass
