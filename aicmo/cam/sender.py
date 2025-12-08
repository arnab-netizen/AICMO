"""
CAM sender.

Phase CAM-4: Send outreach messages through various channels.
"""

from typing import Iterable

from sqlalchemy.orm import Session

from aicmo.cam.domain import OutreachMessage, AttemptStatus, Channel
from aicmo.cam.scheduler import record_attempt


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


# Future enhancement: Integrate with ExecutionService and gateways
# def send_messages_email(db: Session, messages: Iterable[OutreachMessage], email_sender) -> None:
#     """Send messages via email gateway."""
#     pass
#
# def send_messages_linkedin(db: Session, messages: Iterable[OutreachMessage], linkedin_poster) -> None:
#     """Send messages via LinkedIn DM gateway."""
#     pass
