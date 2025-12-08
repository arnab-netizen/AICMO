"""
CAM messaging engine.

Phase CAM-3: Generate personalized outreach messages using AICMO.
"""

from typing import List

from sqlalchemy.orm import Session

from aicmo.cam.domain import (
    Lead,
    Campaign,
    Channel,
    OutreachMessage,
)
from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.domain.base import AicmoBaseModel


class SequenceConfig(AicmoBaseModel):
    """Configuration for outreach sequence per channel."""
    
    channel: Channel
    steps: int = 3
    include_subject_for_email: bool = True


def _to_domain_lead(row: LeadDB) -> Lead:
    """Convert LeadDB to Lead domain model."""
    return Lead(
        id=row.id,
        campaign_id=row.campaign_id,
        name=row.name,
        company=row.company,
        role=row.role,
        email=row.email,
        linkedin_url=row.linkedin_url,
        source=row.source,
        status=row.status,
        notes=row.notes,
    )


def _to_domain_campaign(row: CampaignDB) -> Campaign:
    """Convert CampaignDB to Campaign domain model."""
    return Campaign(
        id=row.id,
        name=row.name,
        description=row.description,
        target_niche=row.target_niche,
        active=row.active,
    )


def generate_messages_for_lead(
    db: Session,
    lead_id: int,
    channel: Channel,
    sequence: SequenceConfig,
) -> List[OutreachMessage]:
    """
    Generate a sequence of OutreachMessage for a lead and channel.
    
    Phase 1: Simple templating.
    Phase 2: Integrate with AICMO strategy/creative modules for smarter personalization.
    
    Args:
        db: Database session
        lead_id: Lead ID
        channel: Communication channel
        sequence: Sequence configuration
        
    Returns:
        List of outreach messages for the sequence
        
    Raises:
        ValueError: If lead or campaign not found
    """
    lead_db = db.query(LeadDB).get(lead_id)
    if not lead_db:
        raise ValueError(f"Lead {lead_id} not found")

    if not lead_db.campaign_id:
        raise ValueError(f"Lead {lead_id} has no campaign_id")

    campaign_db = db.query(CampaignDB).get(lead_db.campaign_id)
    if not campaign_db:
        raise ValueError(f"Campaign {lead_db.campaign_id} not found")

    lead = _to_domain_lead(lead_db)
    campaign = _to_domain_campaign(campaign_db)

    messages: list[OutreachMessage] = []

    # TODO: replace with AICMO-powered messaging (future enhancement)
    for step in range(1, sequence.steps + 1):
        if channel == Channel.EMAIL:
            subject = f"{lead.name}, quick idea for {lead.company or 'your business'}"
        else:
            subject = None

        first_name = lead.name.split(" ")[0]
        company_part = f"like {lead.company}" if lead.company else "in your space"
        niche_part = campaign.target_niche or "your niche"

        body_lines = [
            f"Hi {first_name},",
            "",
            f"I've been looking at brands {company_part} in {niche_part}.",
            "We've built a system that plans and executes content end-to-end (strategy, creatives, posting),",
            "without you having to hire an in-house team.",
        ]

        if step == 1:
            body_lines.append("Would you be open to a quick 15-min chat this week?")
        else:
            body_lines.append("Just bumping this in case it slipped through. Happy to share examples.")

        body = "\n".join(body_lines)

        msg = OutreachMessage(
            lead=lead,
            campaign=campaign,
            channel=channel,
            step_number=step,
            subject=subject,
            body=body,
        )
        messages.append(msg)

    return messages
