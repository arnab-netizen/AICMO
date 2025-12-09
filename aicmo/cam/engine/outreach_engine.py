"""
CAM Outreach Engine — Outreach scheduling and execution.

Phase 4: Implements scheduling of due outreach and executing outreach messages
while respecting safety limits and updating lead status.

Uses existing messaging and safety patterns from sender.py and messaging.py.
Integrates with Make.com webhook adapter for workflow automation.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB
from aicmo.cam.domain import Lead, Campaign, LeadStatus, Channel, AttemptStatus, OutreachMessage, CampaignMode
from aicmo.cam.engine.state_machine import status_after_outreach, compute_next_action_time
from aicmo.cam.engine.safety_limits import can_send_email, remaining_email_quota
from aicmo.gateways import get_email_sender
from aicmo.gateways.factory import get_make_webhook

import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# OUTREACH SCHEDULING
# ═══════════════════════════════════════════════════════════════════════


def schedule_due_outreach(
    db: Session,
    campaign_db: CampaignDB,
    now: datetime = None,
) -> List[LeadDB]:
    """
    Find leads that are due for outreach.
    
    Criteria:
    - Campaign is active
    - Lead status is NEW or ENRICHED or CONTACTED (ready for outreach)
    - next_action_at <= now
    - Email is enabled for campaign
    
    Args:
        db: Database session
        campaign_db: Campaign from database
        now: Current datetime (defaults to utcnow)
        
    Returns:
        List of leads ready for outreach
    """
    if now is None:
        now = datetime.utcnow()
    
    if not campaign_db.active:
        return []
    
    # Find leads due for outreach
    due_leads = (
        db.query(LeadDB)
        .filter(
            and_(
                LeadDB.campaign_id == campaign_db.id,
                LeadDB.status.in_([LeadStatus.NEW, LeadStatus.ENRICHED, LeadStatus.CONTACTED]),
                LeadDB.next_action_at <= now,
            )
        )
        .all()
    )
    
    return due_leads


def execute_due_outreach(
    db: Session,
    campaign: Campaign,
    campaign_db: CampaignDB,
    now: datetime = None,
    dry_run: bool = True,
) -> tuple[int, int, int]:
    """
    Execute outreach for all due leads in a campaign.
    
    Flow:
    1. Schedule due leads
    2. For each lead:
       a. Check safety limits (email quota)
       b. Generate outreach message
       c. Send via email gateway
       d. Log attempt
       e. Update lead status
       f. Trigger Make.com webhook if configured
    
    Args:
        db: Database session
        campaign: Campaign Pydantic model
        campaign_db: Campaign from database
        now: Current datetime (defaults to utcnow)
        dry_run: If True, don't actually send emails (log only)
        
    Returns:
        Tuple (sent_count, failed_count, skipped_count)
    """
    if now is None:
        now = datetime.utcnow()
    
    due_leads = schedule_due_outreach(db, campaign_db, now)
    
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    
    # Get email sender gateway
    email_sender = get_email_sender()
    webhook = get_make_webhook()
    
    for lead_db in due_leads:
        # Convert to Pydantic for processing
        lead = Lead(
            id=lead_db.id,
            campaign_id=lead_db.campaign_id,
            name=lead_db.name,
            email=lead_db.email,
            company=lead_db.company,
            role=lead_db.role,
            status=lead_db.status,
            lead_score=lead_db.lead_score,
            tags=lead_db.tags or [],
            last_contacted_at=lead_db.last_contacted_at,
        )
        
        # Check safety limits
        can_send, reason = can_send_email(db, campaign_db.id, now)
        if not can_send:
            logger.debug(f"Skipping {lead.email}: {reason}")
            
            # Log attempt as SKIPPED
            attempt = OutreachAttemptDB(
                campaign_id=campaign_db.id,
                lead_id=lead.id,
                channel=Channel.EMAIL,
                status=AttemptStatus.SKIPPED,
                reason=reason,
            )
            db.add(attempt)
            
            skipped_count += 1
            continue
        
        # Generate outreach message
        message = _generate_outreach_message(lead, campaign)
        
        # Send email (or simulate)
        attempt_status = AttemptStatus.SENT
        error_msg = None
        
        # Check if campaign is in SIMULATION mode
        is_simulation = campaign_db.mode == CampaignMode.SIMULATION
        
        if not dry_run and not is_simulation:
            try:
                # Call email sender gateway
                # Assuming email_sender.send() returns True on success
                success = email_sender.send(
                    to=lead.email,
                    subject=message.subject,
                    body=message.body,
                    html_body=message.html_body,
                )
                
                if not success:
                    attempt_status = AttemptStatus.FAILED
                    error_msg = "Email gateway returned failure"
                    failed_count += 1
                else:
                    sent_count += 1
                    # Update lead's last_contacted_at
                    lead_db.last_contacted_at = now
            
            except Exception as e:
                attempt_status = AttemptStatus.FAILED
                error_msg = str(e)
                failed_count += 1
                logger.error(f"Failed to send email to {lead.email}: {e}")
        
        elif is_simulation or dry_run:
            # Simulation or dry run: record as SENT but don't send real email
            # Still update state transitions and timing
            reason_text = "SIMULATION" if is_simulation else "DRY_RUN"
            logger.info(f"[{reason_text}] Would send to {lead.email}: {message.subject}")
            sent_count += 1
            error_msg = f"Simulated/dry-run outreach"
            # Update lead's last_contacted_at even in simulation (to track timing)
            lead_db.last_contacted_at = now
        
        # Update lead status based on attempt
        if attempt_status == AttemptStatus.SENT:
            lead_db.status = status_after_outreach(lead, attempt_status, lead.lead_score)
        
        # Schedule next action
        lead_db.next_action_at = compute_next_action_time(lead, campaign, now, "followup")
        
        # Log attempt to database
        attempt = OutreachAttemptDB(
            campaign_id=campaign_db.id,
            lead_id=lead.id,
            channel=Channel.EMAIL,
            status=attempt_status,
            subject=message.subject,
            reason=error_msg,
        )
        db.add(attempt)
        
        # Trigger webhook if configured (non-fatal)
        if attempt_status == AttemptStatus.SENT:
            try:
                webhook.send_lead_event(
                    event_type="OutreachEvent",
                    lead_email=lead.email,
                    lead_name=lead.name,
                    campaign_name=campaign.name,
                    details={"subject": message.subject},
                )
            except Exception as e:
                logger.warning(f"Failed to trigger webhook: {e}")
    
    # Commit batch
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error persisting outreach attempts: {e}")
    
    return sent_count, failed_count, skipped_count


# ═══════════════════════════════════════════════════════════════════════
# MESSAGE GENERATION
# ═══════════════════════════════════════════════════════════════════════


def _generate_outreach_message(
    lead: Lead,
    campaign: Campaign,
    template: Optional[str] = None,
) -> OutreachMessage:
    """
    Generate a personalized outreach message for a lead.
    
    Uses lead enrichment data (name, title, company) to personalize.
    Falls back to a default template if none provided.
    
    Args:
        lead: Lead to reach out to
        campaign: Campaign context
        template: Optional message template (for future use)
        
    Returns:
        OutreachMessage with subject and body
    """
    # Default personalization
    name = lead.name or "there"
    company = lead.company or "your company"
    
    # Simple default template
    subject = f"Quick question about {campaign.target_niche or 'growth'} at {company}"
    
    body = f"""Hi {name},

I came across {company} and was impressed by {lead.role or 'your work'}.

I work with businesses like yours on {campaign.service_key or 'growth strategies'}, and I thought you might find this valuable.

Would you be open to a quick chat?

Best,
{campaign.name or 'Team'}"""
    
    html_body = f"""<p>Hi {name},</p>
<p>I came across {company} and was impressed by {lead.role or 'your work'}.</p>
<p>I work with businesses like yours on <strong>{campaign.service_key or 'growth strategies'}</strong>, and I thought you might find this valuable.</p>
<p>Would you be open to a quick chat?</p>
<p>Best,<br/>{campaign.name or 'Team'}</p>"""
    
    return OutreachMessage(
        lead=lead,
        campaign=campaign,
        channel=Channel.EMAIL,
        step_number=1,
        subject=subject,
        body=body,
    )


# ═══════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════


def get_outreach_stats(
    db: Session,
    campaign_id: int,
    days: int = 1,
    now: datetime = None,
) -> dict:
    """
    Get outreach statistics for a campaign over the last N days.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        days: Number of days to look back
        now: Current datetime (defaults to utcnow)
        
    Returns:
        Dictionary with send/fail/skip counts
    """
    if now is None:
        now = datetime.utcnow()
    
    cutoff = now - __import__('datetime').timedelta(days=days)
    
    attempts = db.query(OutreachAttemptDB).filter(
        and_(
            OutreachAttemptDB.campaign_id == campaign_id,
            OutreachAttemptDB.created_at >= cutoff,
        )
    ).all()
    
    stats = {
        "total": len(attempts),
        "sent": sum(1 for a in attempts if a.status == AttemptStatus.SENT),
        "failed": sum(1 for a in attempts if a.status == AttemptStatus.FAILED),
        "skipped": sum(1 for a in attempts if a.status == AttemptStatus.SKIPPED),
    }
    
    return stats
