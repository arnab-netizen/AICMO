"""
CAM Phase 9: Safety & Limits domain module.

Provides rate limiting, warmup logic, send windows, and DNC/blocklist functionality.
"""

from typing import Optional
from datetime import datetime, date, time
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from aicmo.cam.domain import Channel
from aicmo.cam.db_models import SafetySettingsDB, OutreachAttemptDB, LeadDB, AttemptStatus


class ChannelLimitConfig(BaseModel):
    """Rate limit configuration for a single channel."""
    
    model_config = ConfigDict(from_attributes=True)
    
    channel: str
    max_per_day: int
    warmup_enabled: bool = False
    warmup_start: Optional[int] = None      # max/day on day 1
    warmup_increment: Optional[int] = None  # daily increment
    warmup_max: Optional[int] = None        # cap


class SafetySettings(BaseModel):
    """
    Complete safety and compliance settings for CAM.
    
    Controls rate limits, send windows, and contact restrictions.
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    per_channel_limits: dict[str, ChannelLimitConfig] = Field(default_factory=dict)
    send_window_start: Optional[time] = None  # e.g. 09:00
    send_window_end: Optional[time] = None    # e.g. 18:00
    blocked_domains: list[str] = Field(default_factory=list)
    do_not_contact_emails: list[str] = Field(default_factory=list)
    do_not_contact_lead_ids: list[int] = Field(default_factory=list)


def default_safety_settings() -> SafetySettings:
    """
    Create default safety settings with reasonable limits.
    
    Returns:
        SafetySettings with conservative defaults
    """
    return SafetySettings(
        per_channel_limits={
            "email": ChannelLimitConfig(
                channel="email",
                max_per_day=20,
                warmup_enabled=True,
                warmup_start=5,
                warmup_increment=5,
                warmup_max=20,
            ),
            "linkedin": ChannelLimitConfig(
                channel="linkedin",
                max_per_day=10,
                warmup_enabled=True,
                warmup_start=3,
                warmup_increment=2,
                warmup_max=10,
            ),
            "twitter": ChannelLimitConfig(
                channel="twitter",
                max_per_day=15,
                warmup_enabled=False,
                warmup_start=None,
                warmup_increment=None,
                warmup_max=None,
            ),
        },
        send_window_start=time(9, 0),   # 9 AM
        send_window_end=time(18, 0),    # 6 PM
        blocked_domains=[],
        do_not_contact_emails=[],
        do_not_contact_lead_ids=[],
    )


def get_safety_settings(db: Session) -> SafetySettings:
    """
    Load safety settings from database.
    
    Creates default settings if none exist.
    
    Args:
        db: Database session
        
    Returns:
        Current safety settings
    """
    settings_db = db.get(SafetySettingsDB, 1)
    
    if not settings_db:
        # Create with defaults
        default_settings = default_safety_settings()
        settings_db = SafetySettingsDB(
            id=1,
            data=default_settings.model_dump(mode='json'),
        )
        db.add(settings_db)
        db.commit()
        db.refresh(settings_db)
    
    # Deserialize from JSON
    return SafetySettings(**settings_db.data)


def save_safety_settings(db: Session, settings: SafetySettings) -> SafetySettings:
    """
    Save safety settings to database.
    
    Upserts the singleton settings row.
    
    Args:
        db: Database session
        settings: Settings to save
        
    Returns:
        Saved settings
    """
    settings_db = db.get(SafetySettingsDB, 1)
    
    if settings_db:
        settings_db.data = settings.model_dump(mode='json')
        settings_db.updated_at = datetime.utcnow()
    else:
        settings_db = SafetySettingsDB(
            id=1,
            data=settings.model_dump(mode='json'),
        )
        db.add(settings_db)
    
    db.commit()
    db.refresh(settings_db)
    return settings


def get_daily_limit_for(db: Session, channel: str) -> int:
    """
    Calculate current daily limit for a channel considering warmup.
    
    If warmup is enabled, gradually increases limit from warmup_start
    to warmup_max over multiple days.
    
    Args:
        db: Database session
        channel: Channel name (e.g. "email", "linkedin")
        
    Returns:
        Maximum sends allowed today for this channel
    """
    settings = get_safety_settings(db)
    
    # Get channel config or use default
    if channel not in settings.per_channel_limits:
        return 0
    
    config = settings.per_channel_limits[channel]
    
    if not config.warmup_enabled:
        return config.max_per_day
    
    # Find first attempt for this channel
    first_attempt = (
        db.query(OutreachAttemptDB)
        .filter(OutreachAttemptDB.channel == channel)
        .order_by(OutreachAttemptDB.created_at.asc())
        .first()
    )
    
    if not first_attempt:
        # Day 1
        return config.warmup_start or config.max_per_day
    
    # Calculate days since first attempt
    days_since_first = (date.today() - first_attempt.created_at.date()).days + 1
    
    # Calculate warmup limit
    allowed = config.warmup_start + (days_since_first - 1) * config.warmup_increment
    allowed = min(allowed, config.warmup_max)
    
    return allowed


def can_send_now(db: Session, channel: str) -> bool:
    """
    Check if sending is allowed right now for a channel.
    
    Checks:
    1. Current time within send window
    2. Daily limit not exceeded
    
    Args:
        db: Database session
        channel: Channel name
        
    Returns:
        True if sending is allowed, False otherwise
    """
    settings = get_safety_settings(db)
    
    # Check send window
    if settings.send_window_start and settings.send_window_end:
        now = datetime.utcnow().time()
        if not (settings.send_window_start <= now <= settings.send_window_end):
            return False
    
    # Check daily limit
    daily_limit = get_daily_limit_for(db, channel)
    
    # Count today's successful sends for this channel
    today_start = datetime.combine(date.today(), time.min)
    sends_today = (
        db.query(OutreachAttemptDB)
        .filter(
            OutreachAttemptDB.channel == channel,
            OutreachAttemptDB.status == AttemptStatus.SENT,
            OutreachAttemptDB.created_at >= today_start,
        )
        .count()
    )
    
    return sends_today < daily_limit


def is_contact_allowed(db: Session, lead: LeadDB, email: Optional[str]) -> bool:
    """
    Check if contact with a lead is allowed.
    
    Checks:
    1. Lead not in DNC list
    2. Email not in DNC list
    3. Email domain not blocked
    
    Args:
        db: Database session
        lead: Lead to check
        email: Email address to check (optional)
        
    Returns:
        True if contact is allowed, False otherwise
    """
    settings = get_safety_settings(db)
    
    # Check lead DNC list
    if lead.id in settings.do_not_contact_lead_ids:
        return False
    
    # Check email DNC and blocked domains
    if email:
        # Check email DNC list
        if email.lower() in [e.lower() for e in settings.do_not_contact_emails]:
            return False
        
        # Check blocked domains
        if '@' in email:
            domain = email.split('@')[1].lower()
            if domain in [d.lower() for d in settings.blocked_domains]:
                return False
    
    return True
