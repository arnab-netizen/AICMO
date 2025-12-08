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


# -------------------------------------------------
# CAM-AUTO: Strategy-powered personalization
# -------------------------------------------------


def _extract_angle_from_strategy(strategy) -> str:
    """
    Extract a concise outreach angle from a StrategyDoc.

    This is a safe, generic heuristic. You can tighten it once you know
    the exact shape of strategy_doc.
    """
    from aicmo.domain.strategy import StrategyDoc

    if not isinstance(strategy, StrategyDoc):
        return (
            "We help small businesses turn chaotic, inconsistent marketing "
            "into a predictable, systemized content and acquisition engine."
        )

    # Use primary_goal or strategy_narrative as angle
    angle = strategy.primary_goal

    # Fallback: use strategy_narrative first 200 chars
    if not angle and strategy.strategy_narrative:
        angle = strategy.strategy_narrative[:200] + "..."

    if not angle:
        return (
            "We help small businesses turn chaotic, inconsistent marketing "
            "into a predictable, systemized content and acquisition engine."
        )
    return angle


def generate_personalized_messages_for_lead(
    db: Session,
    lead_id: int,
    channel: Channel,
    sequence: SequenceConfig,
    strategy_doc,
) -> List[OutreachMessage]:
    """
    Strategy-aware version of generate_messages_for_lead:
    uses StrategyDoc to create more compelling outreach.

    Args:
        db: Database session
        lead_id: Lead ID
        channel: Communication channel
        sequence: Sequence configuration
        strategy_doc: StrategyDoc from AICMO strategy engine

    Returns:
        List of personalized outreach messages

    Raises:
        ValueError: If lead or campaign not found
    """
    lead_db = db.get(LeadDB, lead_id)
    if not lead_db:
        raise ValueError(f"Lead {lead_id} not found")

    if not lead_db.campaign_id:
        raise ValueError(f"Lead {lead_id} has no campaign_id")

    campaign_db = db.get(CampaignDB, lead_db.campaign_id)
    if not campaign_db:
        raise ValueError(f"Campaign {lead_db.campaign_id} not found")

    lead = _to_domain_lead(lead_db)
    campaign = _to_domain_campaign(campaign_db)

    angle = _extract_angle_from_strategy(strategy_doc)

    messages: list[OutreachMessage] = []
    for step in range(1, sequence.steps + 1):
        if channel == Channel.EMAIL:
            subject = f"{lead.name.split(' ')[0]}, quick idea for {lead.company or 'your brand'}"
        else:
            subject = None

        intro = f"Hi {lead.name.split(' ')[0]},"
        context = f"I've been studying brands like {lead.company or 'yours'} in {campaign.target_niche or 'your space'}."
        value = angle

        if step == 1:
            call_to_action = "Would you be open to a quick 15-min chat to see if this fits your growth plans?"
        elif step == 2:
            call_to_action = "Just following up in case this slipped past you. Happy to send a 30-day sample plan."
        else:
            call_to_action = "If now's not the right time, no worries at all—just wanted to share this and close the loop."

        body_lines = [intro, "", context, value, "", call_to_action]
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

