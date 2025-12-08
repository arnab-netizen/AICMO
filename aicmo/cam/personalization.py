# aicmo/cam/personalization.py
"""
CAM-AUTO Personalization: Bridge between CAM and AICMO's strategy engine.
Converts CAM leads + campaigns into ClientIntake, generates StrategyDoc for personalized outreach.
"""
from typing import Optional

from sqlalchemy.orm import Session

from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.domain import Lead, Campaign
from aicmo.domain.intake import ClientIntake, GoalMetric
from aicmo.domain.strategy import StrategyDoc
from aicmo.strategy.service import generate_strategy


def _to_domain_lead(row: LeadDB) -> Lead:
    """Convert LeadDB (SQLAlchemy) to Lead (domain model)."""
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
    """Convert CampaignDB (SQLAlchemy) to Campaign (domain model)."""
    return Campaign(
        id=row.id,
        name=row.name,
        description=row.description,
        target_niche=row.target_niche,
        active=row.active,
    )


def build_intake_for_lead_campaign(lead: Lead, campaign: Campaign) -> ClientIntake:
    """
    Normalize a CAM lead + campaign into a ClientIntake that AICMO's
    strategy engine understands.

    This is intentionally generic; you can refine mapping later.
    """
    offers = []
    if campaign.description:
        offers.append(campaign.description)

    target_audiences = []
    if lead.role and lead.company:
        target_audiences.append(f"{lead.role} at {lead.company}")
    elif lead.company:
        target_audiences.append(f"Decision-makers at {lead.company}")

    return ClientIntake(
        brand_name="AICMO (Outbound for Malini)",
        industry=campaign.target_niche or "Marketing / Creative services",
        geography=None,
        offers=offers,
        target_audiences=target_audiences,
        primary_goal=GoalMetric.LEADS,
        primary_goal_description="Book qualified discovery calls for AICMO services",
        kpi_notes="Reply rate, booked calls, closed deals",
        constraints="Respect platform limits. No spammy language.",
        must_include="No mention of AI or automation; present as human-led boutique agency.",
        do_not_do="Do not oversell or promise guaranteed results; no fake urgency.",
    )


def generate_strategy_for_lead(db: Session, lead_id: int) -> StrategyDoc:
    """
    End-to-end:
    - Load LeadDB + CampaignDB
    - Convert to domain Lead + Campaign
    - Build ClientIntake
    - Call AICMO strategy engine
    - Return StrategyDoc
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

    intake = build_intake_for_lead_campaign(lead, campaign)
    strategy_doc = generate_strategy(intake)
    strategy_doc.project_id = None  # optional: later link to a Project
    return strategy_doc
