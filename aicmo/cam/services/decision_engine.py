"""
Phase 4: Campaign decision loop and metrics.

Monitors campaign metrics and makes decisions:
- Pause campaigns with low reply rates
- Flag campaigns for manual review
- Generate metrics snapshots
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from aicmo.cam.db_models import CampaignDB, OutboundEmailDB, InboundEmailDB
from aicmo.cam.config import settings


logger = logging.getLogger(__name__)


@dataclass
class CampaignMetricsSnapshot:
    """Metrics snapshot for a campaign at a point in time."""
    
    campaign_id: int
    campaign_name: str
    sent_count: int
    delivered_count: int
    reply_count: int
    positive_count: int
    negative_count: int
    unsub_count: int
    bounce_count: int
    ooo_count: int
    
    @property
    def reply_rate(self) -> float:
        """Percentage of sent emails that got replies."""
        if self.sent_count == 0:
            return 0.0
        return (self.reply_count / self.sent_count) * 100
    
    @property
    def positive_rate(self) -> float:
        """Percentage of sent emails that got positive replies."""
        if self.sent_count == 0:
            return 0.0
        return (self.positive_count / self.sent_count) * 100
    
    @property
    def bounce_rate(self) -> float:
        """Percentage of sent emails that bounced."""
        if self.sent_count == 0:
            return 0.0
        return (self.bounce_count / self.sent_count) * 100
    
    def __str__(self) -> str:
        """Pretty print metrics."""
        return (
            f"Campaign: {self.campaign_name}\n"
            f"  Sent: {self.sent_count} | Delivered: {self.delivered_count}\n"
            f"  Replies: {self.reply_count} ({self.reply_rate:.1f}%)\n"
            f"    Positive: {self.positive_count} ({self.positive_rate:.1f}%)\n"
            f"    Negative: {self.negative_count}\n"
            f"    Unsubscribe: {self.unsub_count}\n"
            f"  Bounces: {self.bounce_count} ({self.bounce_rate:.1f}%)"
        )


class DecisionEngine:
    """
    Monitor campaigns and make decisions based on metrics.
    
    Rules:
    - If reply_rate < threshold → flag campaign
    - If reply_rate < threshold for N days → auto-pause (if enabled)
    - Manual pause/resume always possible
    """
    
    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session
    
    def compute_campaign_metrics(self, campaign_id: int) -> CampaignMetricsSnapshot:
        """
        Compute current metrics for a campaign.
        
        Args:
            campaign_id: Campaign database ID
        
        Returns:
            CampaignMetricsSnapshot with all metrics
        """
        campaign = self.db.query(CampaignDB).filter_by(id=campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Count sent emails
        sent_count = self.db.query(func.count(OutboundEmailDB.id)).filter(
            and_(
                OutboundEmailDB.campaign_id == campaign_id,
                OutboundEmailDB.status == "SENT",
            )
        ).scalar() or 0
        
        delivered_count = sent_count  # For simplicity, assume all SENT = delivered
        
        # Count replies by classification
        reply_count = self.db.query(func.count(InboundEmailDB.id)).filter(
            and_(
                InboundEmailDB.campaign_id == campaign_id,
                InboundEmailDB.classification.isnot(None),
                InboundEmailDB.classification != "NEUTRAL",
            )
        ).scalar() or 0
        
        positive_count = self.db.query(func.count(InboundEmailDB.id)).filter(
            and_(
                InboundEmailDB.campaign_id == campaign_id,
                InboundEmailDB.classification == "POSITIVE",
            )
        ).scalar() or 0
        
        negative_count = self.db.query(func.count(InboundEmailDB.id)).filter(
            and_(
                InboundEmailDB.campaign_id == campaign_id,
                InboundEmailDB.classification == "NEGATIVE",
            )
        ).scalar() or 0
        
        unsub_count = self.db.query(func.count(InboundEmailDB.id)).filter(
            and_(
                InboundEmailDB.campaign_id == campaign_id,
                InboundEmailDB.classification == "UNSUB",
            )
        ).scalar() or 0
        
        bounce_count = self.db.query(func.count(InboundEmailDB.id)).filter(
            and_(
                InboundEmailDB.campaign_id == campaign_id,
                InboundEmailDB.classification == "BOUNCE",
            )
        ).scalar() or 0
        
        ooo_count = self.db.query(func.count(InboundEmailDB.id)).filter(
            and_(
                InboundEmailDB.campaign_id == campaign_id,
                InboundEmailDB.classification == "OOO",
            )
        ).scalar() or 0
        
        return CampaignMetricsSnapshot(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            sent_count=sent_count,
            delivered_count=delivered_count,
            reply_count=reply_count,
            positive_count=positive_count,
            negative_count=negative_count,
            unsub_count=unsub_count,
            bounce_count=bounce_count,
            ooo_count=ooo_count,
        )
    
    def should_pause_campaign(self, metrics: CampaignMetricsSnapshot) -> Tuple[bool, str]:
        """
        Determine if campaign should be paused based on metrics.
        
        Args:
            metrics: Campaign metrics snapshot
        
        Returns:
            Tuple of (should_pause: bool, reason: str)
        """
        # Check if auto-pause is enabled
        if not settings.CAM_AUTO_PAUSE_ENABLE:
            return (False, "Auto-pause disabled")
        
        # Check minimum sends before evaluating
        if metrics.sent_count < settings.CAM_AUTO_PAUSE_MIN_SENDS_TO_EVALUATE:
            return (
                False,
                f"Not enough sends ({metrics.sent_count} < "
                f"{settings.CAM_AUTO_PAUSE_MIN_SENDS_TO_EVALUATE})",
            )
        
        # Check reply rate threshold
        if metrics.reply_rate < settings.CAM_AUTO_PAUSE_REPLY_RATE_THRESHOLD * 100:
            return (
                True,
                f"Reply rate {metrics.reply_rate:.1f}% below threshold "
                f"{settings.CAM_AUTO_PAUSE_REPLY_RATE_THRESHOLD * 100:.1f}%",
            )
        
        return (False, "Metrics within acceptable range")
    
    def evaluate_campaign(self, campaign_id: int) -> dict:
        """
        Evaluate campaign and generate decision report.
        
        Args:
            campaign_id: Campaign to evaluate
        
        Returns:
            Dictionary with metrics, decision, and recommendation
        """
        metrics = self.compute_campaign_metrics(campaign_id)
        should_pause, reason = self.should_pause_campaign(metrics)
        
        report = {
            "campaign_id": campaign_id,
            "campaign_name": metrics.campaign_name,
            "metrics": {
                "sent": metrics.sent_count,
                "delivered": metrics.delivered_count,
                "replies": metrics.reply_count,
                "reply_rate": f"{metrics.reply_rate:.1f}%",
                "positive_rate": f"{metrics.positive_rate:.1f}%",
                "bounce_rate": f"{metrics.bounce_rate:.1f}%",
                "positive": metrics.positive_count,
                "negative": metrics.negative_count,
                "unsub": metrics.unsub_count,
                "bounce": metrics.bounce_count,
                "ooo": metrics.ooo_count,
            },
            "decision": "PAUSE" if should_pause else "CONTINUE",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Campaign {campaign_id} evaluation: {report['decision']} - {reason}")
        return report
    
    def is_configured(self) -> bool:
        """DecisionEngine is always configured (no external dependencies)."""
        return True
    
    def health(self) -> dict:
        """Return health status of decision module."""
        from aicmo.cam.contracts import ModuleHealthModel
        try:
            return ModuleHealthModel(
                module_name="DecisionModule",
                is_healthy=True,
                status="READY",
                message="Decision engine operational"
            ).dict()
        except Exception as e:
            return ModuleHealthModel(
                module_name="DecisionModule",
                is_healthy=False,
                status="ERROR",
                message=str(e)
            ).dict()
