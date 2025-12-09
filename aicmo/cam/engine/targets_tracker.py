"""
CAM Targets Tracker — Campaign goal tracking and metrics.

Phase 4: Computes campaign metrics (leads per status, conversion rates) and
determines if campaign goals have been met.

Uses extended Campaign fields:
- campaign.target_clients (int, optional) - goal number of leads
- campaign.target_mrr (float, optional) - target monthly recurring revenue
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.cam.domain import LeadStatus


# ═══════════════════════════════════════════════════════════════════════
# METRICS DATACLASS
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class CampaignMetrics:
    """
    Metrics for a campaign's lead acquisition progress.
    
    Attributes:
        campaign_id: Campaign ID
        total_leads: Total leads discovered
        status_new: Count of NEW status leads
        status_enriched: Count of ENRICHED status leads
        status_contacted: Count of CONTACTED status leads
        status_replied: Count of REPLIED status leads
        status_qualified: Count of QUALIFIED status leads
        status_lost: Count of LOST status leads
        
        conversion_rate: Qualified / Total (0.0-1.0)
        
        target_clients: Goal from campaign config
        qualified_pct: Qualified leads as % of target
        target_mrr: Goal MRR from campaign config
    """
    
    campaign_id: int
    total_leads: int = 0
    status_new: int = 0
    status_enriched: int = 0
    status_contacted: int = 0
    status_replied: int = 0
    status_qualified: int = 0
    status_lost: int = 0
    
    conversion_rate: float = 0.0
    target_clients: Optional[int] = None
    qualified_pct: float = 0.0
    target_mrr: Optional[float] = None
    
    def __str__(self) -> str:
        """Pretty-print metrics."""
        lines = [
            f"Campaign {self.campaign_id} Metrics:",
            f"  Total leads: {self.total_leads}",
            f"  Status breakdown:",
            f"    NEW: {self.status_new}",
            f"    ENRICHED: {self.status_enriched}",
            f"    CONTACTED: {self.status_contacted}",
            f"    REPLIED: {self.status_replied}",
            f"    QUALIFIED: {self.status_qualified}",
            f"    LOST: {self.status_lost}",
            f"  Conversion rate: {self.conversion_rate:.1%}",
        ]
        if self.target_clients:
            lines.append(f"  Target: {self.target_clients} clients ({self.qualified_pct:.1%} achieved)")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# METRICS COMPUTATION
# ═══════════════════════════════════════════════════════════════════════


def compute_campaign_metrics(
    db: Session,
    campaign_id: int,
) -> CampaignMetrics:
    """
    Compute comprehensive metrics for a campaign.
    
    Queries LeadDB to count leads per status and calculates conversion rates.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        
    Returns:
        CampaignMetrics with full breakdown
    """
    # Get campaign config
    campaign = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign:
        return CampaignMetrics(campaign_id=campaign_id)
    
    # Count leads per status
    total = db.query(func.count(LeadDB.id)).filter(LeadDB.campaign_id == campaign_id).scalar() or 0
    
    status_counts = {}
    for status in LeadStatus:
        count = (
            db.query(func.count(LeadDB.id))
            .filter(LeadDB.campaign_id == campaign_id, LeadDB.status == status)
            .scalar()
        ) or 0
        status_counts[status] = count
    
    # Calculate conversion rate
    qualified_count = status_counts.get(LeadStatus.QUALIFIED, 0)
    conversion_rate = qualified_count / total if total > 0 else 0.0
    
    # Calculate progress to target
    qualified_pct = 0.0
    if campaign.target_clients and campaign.target_clients > 0:
        qualified_pct = min(1.0, qualified_count / campaign.target_clients)
    
    return CampaignMetrics(
        campaign_id=campaign_id,
        total_leads=total,
        status_new=status_counts.get(LeadStatus.NEW, 0),
        status_enriched=status_counts.get(LeadStatus.ENRICHED, 0),
        status_contacted=status_counts.get(LeadStatus.CONTACTED, 0),
        status_replied=status_counts.get(LeadStatus.REPLIED, 0),
        status_qualified=status_counts.get(LeadStatus.QUALIFIED, 0),
        status_lost=status_counts.get(LeadStatus.LOST, 0),
        conversion_rate=conversion_rate,
        target_clients=campaign.target_clients,
        qualified_pct=qualified_pct,
        target_mrr=campaign.target_mrr,
    )


# ═══════════════════════════════════════════════════════════════════════
# GOAL CHECKING
# ═══════════════════════════════════════════════════════════════════════


def is_campaign_goal_met(
    db: Session,
    campaign: CampaignDB,
    metrics: Optional[CampaignMetrics] = None,
) -> tuple[bool, str]:
    """
    Determine if a campaign has met its goals.
    
    A campaign goal is met if:
    - target_clients is set AND qualified_count >= target_clients, OR
    - No goals set (campaign continues indefinitely)
    
    Args:
        db: Database session
        campaign: Campaign to check
        metrics: Optional pre-computed metrics (computed if not provided)
        
    Returns:
        Tuple (goal_met: bool, reason: str)
    """
    # If no goals set, goal is never "met" (continues indefinitely)
    if not campaign.target_clients and not campaign.target_mrr:
        return False, "No goals set for this campaign"
    
    # Compute metrics if not provided
    if metrics is None:
        metrics = compute_campaign_metrics(db, campaign.id)
    
    # Check target_clients
    if campaign.target_clients and campaign.target_clients > 0:
        if metrics.status_qualified >= campaign.target_clients:
            return True, f"Target clients reached: {metrics.status_qualified}/{campaign.target_clients}"
    
    # Check target_mrr (not tracked per-lead in this phase, so skip)
    # This would require deal value tracking in future phases
    
    return False, "Goals not yet met"


def should_pause_campaign(
    db: Session,
    campaign: CampaignDB,
) -> tuple[bool, str]:
    """
    Determine if a campaign should be automatically paused.
    
    Pause if:
    - Goal is met, OR
    - Too many LOST leads (>50%), OR
    - Campaign has been running >90 days without qualified leads
    
    Args:
        db: Database session
        campaign: Campaign to check
        
    Returns:
        Tuple (should_pause: bool, reason: str)
    """
    metrics = compute_campaign_metrics(db, campaign.id)
    
    # Check if goal is met
    goal_met, goal_reason = is_campaign_goal_met(db, campaign, metrics)
    if goal_met:
        return True, f"Campaign goal met: {goal_reason}"
    
    # Check if too many lost leads
    if metrics.total_leads > 10:
        lost_rate = metrics.status_lost / metrics.total_leads
        if lost_rate > 0.5:
            return True, f"Too many lost leads ({lost_rate:.1%})"
    
    # Check campaign age
    if campaign.created_at:
        age_days = (datetime.utcnow() - campaign.created_at).days
        if age_days > 90 and metrics.status_qualified == 0:
            return True, "Campaign running >90 days with no qualified leads"
    
    return False, "Campaign should continue"
