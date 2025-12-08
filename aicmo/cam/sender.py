"""
CAM sender.

Phase CAM-4: Send outreach messages through various channels.
Phase CAM-6 (AUTO): Automated sending via email and social gateways.
Phase CAM-9: Safety checks (rate limits, warmup, send windows, DNC lists).
"""

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from aicmo.cam.domain import OutreachMessage, AttemptStatus, Channel
from aicmo.cam.scheduler import record_attempt
from aicmo.cam.safety import can_send_now, is_contact_allowed
from aicmo.gateways.interfaces import EmailSender, SocialPoster


def send_messages_console(
    db: Session,
    messages: Iterable[OutreachMessage],
) -> None:
    """
    v0: Print messages to console for manual sending via LinkedIn/email.
    
    Records attempts as PENDING for tracking.
    
    Args:
        db: Database session
        messages: Outreach messages to print
    """
    for msg in messages:
        print("=" * 80)
        print(f"Lead: {msg.lead.name} | {msg.lead.company} | {msg.channel}")
        print(f"Step: {msg.step_number}")
        if msg.subject:
            print(f"Subject: {msg.subject}")
        print()
        print(msg.body)
        print("=" * 80)

        record_attempt(
            db=db,
            lead_id=msg.lead.id,
            campaign_id=msg.campaign.id,
            channel=msg.channel,
            step_number=msg.step_number,
            status=AttemptStatus.PENDING,
        )


async def send_messages_email_auto(
    db: Session,
    messages: Iterable[OutreachMessage],
    email_sender: EmailSender,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
) -> None:
    """
    CAM-AUTO: Send messages via email gateway with automatic delivery.
    
    Phase 9: Enforces safety checks (rate limits, send windows, DNC lists).
    
    Records attempts as SENT on success, FAILED on error, or SKIPPED if safety checks fail.
    
    Args:
        db: Database session
        messages: Outreach messages to send
        email_sender: EmailSender gateway implementation
        from_email: Sender email address (defaults to gateway config)
        from_name: Sender display name (defaults to gateway config)
    """
    for msg in messages:
        # Phase 9: Safety checks before sending
        
        # Check 1: Can we send on this channel right now? (time window + daily limit)
        if not can_send_now(db, msg.channel):
            record_attempt(
                db=db,
                lead_id=msg.lead.id,
                campaign_id=msg.campaign.id,
                channel=msg.channel,
                step_number=msg.step_number,
                status=AttemptStatus.SKIPPED,
                last_error="safety_limit: outside send window or daily limit reached",
            )
            continue
        
        # Check 2: Is this contact allowed? (DNC lists + blocked domains)
        if not is_contact_allowed(db, msg.lead, msg.lead.email):
            record_attempt(
                db=db,
                lead_id=msg.lead.id,
                campaign_id=msg.campaign.id,
                channel=msg.channel,
                step_number=msg.step_number,
                status=AttemptStatus.SKIPPED,
                last_error="dnc: contact on do-not-contact list or blocked domain",
            )
            continue
        
        # Safety checks passed, proceed with sending
        try:
            # Convert plain text body to HTML for better formatting
            html_body = msg.body.replace("\n", "<br>")
            
            result = await email_sender.send_email(
                to_email=msg.lead.email,
                subject=msg.subject or f"Message for {msg.lead.name}",
                html_body=html_body,
                from_email=from_email,
                from_name=from_name,
                metadata={
                    "lead_id": msg.lead.id,
                    "campaign_id": msg.campaign.id,
                    "step_number": msg.step_number,
                },
            )
            
            if result.status.value == "success":
                record_attempt(
                    db=db,
                    lead_id=msg.lead.id,
                    campaign_id=msg.campaign.id,
                    channel=msg.channel,
                    step_number=msg.step_number,
                    status=AttemptStatus.SENT,
                    last_error=f"platform_id: {result.platform_message_id}" if result.platform_message_id else None,
                )
            else:
                record_attempt(
                    db=db,
                    lead_id=msg.lead.id,
                    campaign_id=msg.campaign.id,
                    channel=msg.channel,
                    step_number=msg.step_number,
                    status=AttemptStatus.FAILED,
                    last_error=result.error_message,
                )
        except Exception as e:
            # Record failed attempt on any exception
            record_attempt(
                db=db,
                lead_id=msg.lead.id,
                campaign_id=msg.campaign.id,
                channel=msg.channel,
                step_number=msg.step_number,
                status=AttemptStatus.FAILED,
                last_error=str(e),
            )


async def send_messages_social_auto(
    db: Session,
    messages: Iterable[OutreachMessage],
    social_poster: SocialPoster,
) -> None:
    """
    CAM-AUTO: Send messages via social media gateway (LinkedIn DM, etc.).
    
    Phase 9: Enforces safety checks (rate limits, send windows, DNC lists).
    
    Records attempts as SENT on success, FAILED on error, or SKIPPED if safety checks fail.
    
    Args:
        db: Database session
        messages: Outreach messages to send
        social_poster: SocialPoster gateway implementation (e.g., LinkedInPoster)
    """
    for msg in messages:
        # Phase 9: Safety checks before sending
        
        # Check 1: Can we send on this channel right now? (time window + daily limit)
        if not can_send_now(db, msg.channel):
            record_attempt(
                db=db,
                lead_id=msg.lead.id,
                campaign_id=msg.campaign.id,
                channel=msg.channel,
                step_number=msg.step_number,
                status=AttemptStatus.SKIPPED,
                last_error="safety_limit: outside send window or daily limit reached",
            )
            continue
        
        # Check 2: Is this contact allowed? (DNC lists + blocked domains)
        # For social, we check linkedin_url instead of email
        if not is_contact_allowed(db, msg.lead, None):
            record_attempt(
                db=db,
                lead_id=msg.lead.id,
                campaign_id=msg.campaign.id,
                channel=msg.channel,
                step_number=msg.step_number,
                status=AttemptStatus.SKIPPED,
                last_error="dnc: contact on do-not-contact list",
            )
            continue
        
        # Safety checks passed, proceed with sending
        try:
            # For LinkedIn DMs, we'd use a direct message API
            # Mock implementation assumes social_poster has a send_dm method
            # In production, this would integrate with LinkedIn's messaging API
            
            # Create a mock ContentItem for the social poster
            from aicmo.domain.execution import ContentItem
            
            content = ContentItem(
                project_id=f"cam_{msg.campaign.id}",
                platform=social_poster.get_platform_name(),
                content_type="dm",  # Direct message
                caption=msg.body,
                metadata={
                    "lead_id": msg.lead.id,
                    "lead_name": msg.lead.name,
                    "step_number": msg.step_number,
                    "linkedin_url": msg.lead.linkedin_url,
                },
            )
            
            result = await social_poster.post(content)
            
            if result.status.value == "success":
                record_attempt(
                    db=db,
                    lead_id=msg.lead.id,
                    campaign_id=msg.campaign.id,
                    channel=msg.channel,
                    step_number=msg.step_number,
                    status=AttemptStatus.SENT,
                    last_error=f"platform_id: {result.platform_post_id}" if result.platform_post_id else None,
                )
            else:
                record_attempt(
                    db=db,
                    lead_id=msg.lead.id,
                    campaign_id=msg.campaign.id,
                    channel=msg.channel,
                    step_number=msg.step_number,
                    status=AttemptStatus.FAILED,
                    last_error=result.error_message,
                )
        except Exception as e:
            # Record failed attempt on any exception
            record_attempt(
                db=db,
                lead_id=msg.lead.id,
                campaign_id=msg.campaign.id,
                channel=msg.channel,
                step_number=msg.step_number,
                status=AttemptStatus.FAILED,
                last_error=str(e),
            )


# Legacy phase 4 console sending (preserved for backwards compatibility)
# Future enhancement: Integrate with ExecutionService and gateways
# def send_messages_email(db: Session, messages: Iterable[OutreachMessage], email_sender) -> None:
#     """Send messages via email gateway."""
#     pass
#
# def send_messages_linkedin(db: Session, messages: Iterable[OutreachMessage], linkedin_poster) -> None:
#     """Send messages via LinkedIn DM gateway."""
#     pass
