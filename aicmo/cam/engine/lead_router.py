"""
Phase 5: Lead Routing Engine

Routes qualified leads to appropriate nurture sequences based on tier and engagement level.

Components:
- RoutingRules: Configuration for lead routing
- LeadRouter: Main routing engine
- RoutingMetrics: Operation tracking
- ContentSequence: Pre-defined nurture sequences
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadStatus, LeadSource
from aicmo.cam.db_models import LeadDB

logger = logging.getLogger(__name__)


class ContentSequenceType(Enum):
    """Types of nurture sequences."""
    AGGRESSIVE_CLOSE = "aggressive_close"      # HOT leads: 7-10 day close
    REGULAR_NURTURE = "regular_nurture"        # WARM leads: 14-21 day nurture
    LONG_TERM_NURTURE = "long_term_nurture"    # COOL leads: 30+ day nurture
    COLD_OUTREACH = "cold_outreach"            # COLD leads: 60+ day education


class RoutingStatus(Enum):
    """Status of routing operation."""
    ROUTED = "routed"
    ALREADY_ROUTED = "already_routed"
    QUALIFICATION_PENDING = "qualification_pending"
    REJECTED_LEAD = "rejected_lead"


@dataclass
class ContentSequence:
    """Definition of a content nurture sequence."""
    
    name: str
    """Sequence name (e.g., 'Aggressive Close')."""
    
    sequence_type: ContentSequenceType
    """Type of sequence."""
    
    duration_days: int
    """Expected duration in days."""
    
    email_count: int
    """Number of emails in sequence."""
    
    goal: str
    """Primary goal of sequence (e.g., 'Schedule demo')."""
    
    description: str = ""
    """Detailed description of sequence flow."""
    
    @staticmethod
    def hot_sequence() -> "ContentSequence":
        """Aggressive sequence for HOT leads."""
        return ContentSequence(
            name="Aggressive Close - HOT Leads",
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            duration_days=7,
            email_count=3,
            goal="Schedule demo within 7 days",
            description="Immediate outreach with value prop + demo offer + follow-up"
        )
    
    @staticmethod
    def warm_sequence() -> "ContentSequence":
        """Regular sequence for WARM leads."""
        return ContentSequence(
            name="Regular Nurture - WARM Leads",
            sequence_type=ContentSequenceType.REGULAR_NURTURE,
            duration_days=14,
            email_count=4,
            goal="Establish interest + qualify need",
            description="Paced outreach with educational content + soft offer"
        )
    
    @staticmethod
    def cool_sequence() -> "ContentSequence":
        """Long-term sequence for COOL leads."""
        return ContentSequence(
            name="Long-Term Nurture - COOL Leads",
            sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
            duration_days=30,
            email_count=6,
            goal="Provide value + build relationship",
            description="Slow burn with high-value content + educational series"
        )
    
    @staticmethod
    def cold_sequence() -> "ContentSequence":
        """Education sequence for COLD leads."""
        return ContentSequence(
            name="Cold Outreach - COLD Leads",
            sequence_type=ContentSequenceType.COLD_OUTREACH,
            duration_days=60,
            email_count=8,
            goal="Introduce product + establish credibility",
            description="Educational content focusing on industry trends + use cases"
        )


@dataclass
class RoutingRules:
    """Configuration for lead routing logic."""
    
    enable_auto_routing: bool = True
    """Whether to enable automatic lead routing."""
    
    hot_sequence: ContentSequence = field(default_factory=ContentSequence.hot_sequence)
    """Sequence for HOT leads."""
    
    warm_sequence: ContentSequence = field(default_factory=ContentSequence.warm_sequence)
    """Sequence for WARM leads."""
    
    cool_sequence: ContentSequence = field(default_factory=ContentSequence.cool_sequence)
    """Sequence for COOL leads."""
    
    cold_sequence: ContentSequence = field(default_factory=ContentSequence.cold_sequence)
    """Sequence for COLD leads."""
    
    hot_tier_min_score: float = 0.85
    """Minimum ICP score for HOT tier."""
    
    warm_tier_min_score: float = 0.70
    """Minimum ICP score for WARM tier."""
    
    cool_tier_min_score: float = 0.50
    """Minimum ICP score for COOL tier."""
    
    intent_boost_enabled: bool = True
    """Whether high intent boosts tier assignment."""
    
    intent_score_threshold: float = 0.5
    """Intent score required for tier boost."""
    
    def to_dict(self) -> Dict:
        """Convert rules to dictionary for logging/storage."""
        return {
            "enable_auto_routing": self.enable_auto_routing,
            "hot_tier_min_score": self.hot_tier_min_score,
            "warm_tier_min_score": self.warm_tier_min_score,
            "cool_tier_min_score": self.cool_tier_min_score,
            "intent_boost_enabled": self.intent_boost_enabled,
            "intent_score_threshold": self.intent_score_threshold,
        }


@dataclass
class RoutingDecision:
    """Decision from routing a single lead."""
    
    lead_id: int
    """Lead ID."""
    
    status: RoutingStatus
    """Routing status."""
    
    sequence_type: Optional[ContentSequenceType]
    """Assigned sequence type."""
    
    reasoning: str
    """Human-readable reasoning."""
    
    scheduled_for: Optional[datetime] = None
    """When first email should be sent."""
    
    boosted_by_intent: bool = False
    """Whether tier was boosted due to high intent."""


@dataclass
class RoutingMetrics:
    """Metrics from batch routing operation."""
    
    processed_count: int = 0
    """Total leads routed."""
    
    routed_count: int = 0
    """Successfully routed leads."""
    
    hot_count: int = 0
    """Leads routed to HOT sequence."""
    
    warm_count: int = 0
    """Leads routed to WARM sequence."""
    
    cool_count: int = 0
    """Leads routed to COOL sequence."""
    
    cold_count: int = 0
    """Leads routed to COLD sequence."""
    
    skipped_count: int = 0
    """Leads not routed (already routed or pending)."""
    
    rejected_count: int = 0
    """Rejected leads not routed."""
    
    duration_seconds: float = 0.0
    """Time to complete routing."""
    
    errors: int = 0
    """Number of routing errors."""
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        total_routed = self.hot_count + self.warm_count + self.cool_count + self.cold_count
        
        return {
            "processed_count": self.processed_count,
            "routed_count": self.routed_count,
            "hot_count": self.hot_count,
            "warm_count": self.warm_count,
            "cool_count": self.cool_count,
            "cold_count": self.cold_count,
            "skipped_count": self.skipped_count,
            "rejected_count": self.rejected_count,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
            "hot_ratio": self.hot_count / max(1, total_routed),
            "warm_ratio": self.warm_count / max(1, total_routed),
            "cool_ratio": self.cool_count / max(1, total_routed),
            "cold_ratio": self.cold_count / max(1, total_routed),
        }


class LeadRouter:
    """Main lead routing engine."""
    
    def __init__(self, rules: RoutingRules):
        """
        Initialize lead router.
        
        Args:
            rules: Routing rules and configuration
        """
        self.rules = rules
    
    def route_single_lead(self, lead: Lead) -> RoutingDecision:
        """
        Route a single lead to appropriate sequence.
        
        Args:
            lead: Lead to route
        
        Returns:
            RoutingDecision with assignment
        """
        # Check lead status - convert string to enum if needed
        status = lead.status if isinstance(lead.status, LeadStatus) else LeadStatus(lead.status)
        
        # Check if already routed
        if status == LeadStatus.ROUTED:
            return RoutingDecision(
                lead_id=lead.id,
                status=RoutingStatus.ALREADY_ROUTED,
                sequence_type=None,
                reasoning="Lead already routed to sequence"
            )
        
        # Check if lost/rejected
        if status == LeadStatus.LOST:
            return RoutingDecision(
                lead_id=lead.id,
                status=RoutingStatus.REJECTED_LEAD,
                sequence_type=None,
                reasoning="Lead was rejected during qualification"
            )
        
        # Check if qualified or in manual review
        if status not in [LeadStatus.QUALIFIED, LeadStatus.MANUAL_REVIEW]:
            return RoutingDecision(
                lead_id=lead.id,
                status=RoutingStatus.QUALIFICATION_PENDING,
                sequence_type=None,
                reasoning=f"Lead status is {status.value}, not yet qualified"
            )
        
        # Get ICP score
        icp_score = lead.lead_score or 0.0
        
        # Calculate intent boost
        intent_boost = False
        if self.rules.intent_boost_enabled and lead.enrichment_data:
            intent_score = self._calculate_intent_score(lead.enrichment_data)
            if intent_score >= self.rules.intent_score_threshold:
                intent_boost = True
        
        # Assign tier and sequence
        sequence_type = self._determine_sequence(icp_score, intent_boost)
        
        # Create routing decision
        decision = RoutingDecision(
            lead_id=lead.id,
            status=RoutingStatus.ROUTED,
            sequence_type=sequence_type,
            reasoning=self._create_reasoning(lead, icp_score, intent_boost),
            boosted_by_intent=intent_boost,
            scheduled_for=datetime.utcnow()
        )
        
        return decision
    
    def batch_route_leads(
        self,
        db: Session,
        campaign_id: int,
        max_leads: int = 1000
    ) -> RoutingMetrics:
        """
        Route all routable leads in campaign.
        
        Args:
            db: Database session
            campaign_id: Campaign ID
            max_leads: Maximum leads to route
        
        Returns:
            RoutingMetrics with results
        """
        if not self.rules.enable_auto_routing:
            return RoutingMetrics()
        
        start_time = datetime.utcnow()
        metrics = RoutingMetrics()
        
        try:
            # Query routable leads (QUALIFIED or MANUAL_REVIEW, not ROUTED)
            leads = db.query(LeadDB).filter(
                LeadDB.campaign_id == campaign_id,
                LeadDB.status.in_([LeadStatus.QUALIFIED.value, LeadStatus.MANUAL_REVIEW.value])
            ).limit(max_leads).all()
            
            for lead_db in leads:
                metrics.processed_count += 1
                
                # Convert to domain model
                lead = Lead(
                    id=lead_db.id,
                    campaign_id=lead_db.campaign_id,
                    name=lead_db.name,
                    email=lead_db.email,
                    company=lead_db.company,
                    role=lead_db.role,
                    source=LeadSource(lead_db.source) if lead_db.source else LeadSource.CSV,
                    status=LeadStatus(lead_db.status) if lead_db.status else LeadStatus.NEW,
                    lead_score=lead_db.lead_score,
                    enrichment_data=lead_db.enrichment_data or {}
                )
                
                # Route
                decision = self.route_single_lead(lead)
                
                if decision.status == RoutingStatus.ROUTED:
                    metrics.routed_count += 1
                    
                    # Update database
                    lead_db.status = LeadStatus.ROUTED.value
                    lead_db.notes = decision.reasoning
                    lead_db.routing_sequence = decision.sequence_type.value
                    lead_db.sequence_start_at = decision.scheduled_for
                    
                    # Track by tier
                    if decision.sequence_type == ContentSequenceType.AGGRESSIVE_CLOSE:
                        metrics.hot_count += 1
                    elif decision.sequence_type == ContentSequenceType.REGULAR_NURTURE:
                        metrics.warm_count += 1
                    elif decision.sequence_type == ContentSequenceType.LONG_TERM_NURTURE:
                        metrics.cool_count += 1
                    else:
                        metrics.cold_count += 1
                
                elif decision.status == RoutingStatus.REJECTED_LEAD:
                    metrics.rejected_count += 1
                elif decision.status == RoutingStatus.ALREADY_ROUTED:
                    metrics.skipped_count += 1
                else:
                    metrics.skipped_count += 1
            
            # Commit transaction
            db.commit()
            
        except Exception as e:
            db.rollback()
            metrics.errors += 1
            logger.error(f"Error routing leads: {e}")
        
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            metrics.duration_seconds = duration
        
        return metrics
    
    def _determine_sequence(self, icp_score: float, intent_boost: bool) -> ContentSequenceType:
        """
        Determine appropriate sequence for lead.
        
        Args:
            icp_score: ICP fit score (0.0-1.0)
            intent_boost: Whether to boost tier
        
        Returns:
            ContentSequenceType
        """
        # Apply intent boost by increasing score
        effective_score = icp_score
        if intent_boost:
            effective_score = min(1.0, icp_score + 0.15)
        
        # Determine tier
        if effective_score >= self.rules.hot_tier_min_score:
            return ContentSequenceType.AGGRESSIVE_CLOSE
        elif effective_score >= self.rules.warm_tier_min_score:
            return ContentSequenceType.REGULAR_NURTURE
        elif effective_score >= self.rules.cool_tier_min_score:
            return ContentSequenceType.LONG_TERM_NURTURE
        else:
            return ContentSequenceType.COLD_OUTREACH
    
    def _calculate_intent_score(self, enrichment_data: Dict) -> float:
        """
        Calculate intent score from enrichment data.
        
        Args:
            enrichment_data: Lead enrichment data
        
        Returns:
            Intent score (0.0-1.0)
        """
        signals = [
            enrichment_data.get("recent_job_change", False),
            enrichment_data.get("company_funded_recently", False),
            enrichment_data.get("company_hiring", False),
            enrichment_data.get("recent_activity", False),
            enrichment_data.get("is_decision_maker", False),
            enrichment_data.get("has_budget_authority", False),
        ]
        
        signal_count = sum(1 for signal in signals if signal)
        return min(1.0, signal_count / 6.0)
    
    def _create_reasoning(self, lead: Lead, icp_score: float, intent_boost: bool) -> str:
        """
        Create human-readable reasoning for routing decision.
        
        Args:
            lead: Lead being routed
            icp_score: ICP score
            intent_boost: Whether intent boosted tier
        
        Returns:
            Reasoning string
        """
        boost_text = " (boosted by strong intent signals)" if intent_boost else ""
        return f"Routed with ICP fit {icp_score:.2f}{boost_text}"
