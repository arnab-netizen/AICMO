"""
Lead Scoring Engine (Phase D-3).

Implements ICP-based and opportunity-based scoring for intelligent lead prioritization.
Classifies leads into opportunity tiers (HOT, WARM, COOL, COLD) for outreach sequencing.

Features:
- ICP fit scoring (company size, industry, revenue alignment)
- Opportunity scoring (job title, seniority, buying signals)
- Lead tier classification (HOT/WARM/COOL/COLD)
- Batch processing with database updates
- Comprehensive metrics tracking
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
from enum import Enum

from sqlalchemy.orm import Session
from pydantic import BaseModel

from aicmo.cam.domain import Lead, Campaign
from aicmo.cam.db_models import LeadDB


class LeadTier(str, Enum):
    """Lead opportunity tier based on combined scoring."""
    HOT = "HOT"      # Score >= 0.85 - Priority outreach
    WARM = "WARM"    # Score 0.65-0.84 - Secondary outreach
    COOL = "COOL"    # Score 0.40-0.64 - Lower priority
    COLD = "COLD"    # Score < 0.40 - Nurture only


class CompanySize(str, Enum):
    """Company size classification."""
    STARTUP = "startup"
    SMALL = "small"        # 10-50 employees
    MEDIUM = "medium"      # 50-500 employees
    ENTERPRISE = "enterprise"  # 500+ employees


class ICPScorer:
    """
    ICP (Ideal Customer Profile) fit scorer.
    
    Evaluates how well a lead's company matches campaign target profile
    based on company size, industry, revenue, and location.
    """

    def __init__(
        self,
        size_weight: float = 0.30,
        industry_weight: float = 0.30,
        revenue_weight: float = 0.25,
        location_weight: float = 0.15,
    ):
        """
        Initialize ICP scorer with scoring weights.
        
        Args:
            size_weight: Weight for company size fit (0.0-1.0)
            industry_weight: Weight for industry match (0.0-1.0)
            revenue_weight: Weight for revenue alignment (0.0-1.0)
            location_weight: Weight for geographic fit (0.0-1.0)
        """
        self.size_weight = size_weight
        self.industry_weight = industry_weight
        self.revenue_weight = revenue_weight
        self.location_weight = location_weight

    def compute_icp_fit(self, lead: Lead, campaign: Campaign) -> float:
        """
        Compute ICP fit score (0.0-1.0) for lead vs campaign.
        
        Combines:
        - Company size match vs target_company_size
        - Industry alignment with campaign vertical
        - Revenue fit vs budget constraints
        - Location relevance
        
        Args:
            lead: Lead domain model
            campaign: Campaign domain model
            
        Returns:
            ICP fit score (0.0-1.0), higher = better fit
        """
        if not campaign or not lead or not lead.enrichment_data:
            return 0.5  # Default neutral if missing context

        enrichment = lead.enrichment_data or {}

        # Size fit: extract company size from enrichment
        size_score = self._score_company_size(
            enrichment.get("company_size"),
            campaign.target_company_size if hasattr(campaign, "target_company_size") else None,
        )

        # Industry fit: check if industry matches campaign vertical
        industry_score = self._score_industry(
            enrichment.get("industry"),
            campaign.target_industry if hasattr(campaign, "target_industry") else None,
        )

        # Revenue fit: check if revenue is in acceptable range
        revenue_score = self._score_revenue(
            enrichment.get("annual_revenue"),
            campaign.target_revenue_min if hasattr(campaign, "target_revenue_min") else None,
            campaign.target_revenue_max if hasattr(campaign, "target_revenue_max") else None,
        )

        # Location fit: geographic relevance
        location_score = self._score_location(
            enrichment.get("company_location"),
            campaign.target_location if hasattr(campaign, "target_location") else None,
        )

        # Weighted combination
        icp_score = (
            size_score * self.size_weight
            + industry_score * self.industry_weight
            + revenue_score * self.revenue_weight
            + location_score * self.location_weight
        )

        return min(1.0, max(0.0, icp_score))

    def _score_company_size(
        self, company_size: Optional[str], target_size: Optional[str]
    ) -> float:
        """Score company size fit."""
        if not company_size or not target_size:
            return 0.5  # Neutral if unknown

        # Exact match gets full points
        if company_size.lower() == target_size.lower():
            return 1.0

        # Adjacent sizes get partial credit
        size_hierarchy = [
            CompanySize.STARTUP,
            CompanySize.SMALL,
            CompanySize.MEDIUM,
            CompanySize.ENTERPRISE,
        ]

        try:
            company_idx = next(
                i for i, s in enumerate(size_hierarchy) if s.value == company_size.lower()
            )
            target_idx = next(
                i for i, s in enumerate(size_hierarchy) if s.value == target_size.lower()
            )
            distance = abs(company_idx - target_idx)
            return max(0.5, 1.0 - (distance * 0.2))
        except (StopIteration, AttributeError, ValueError):
            return 0.5

    def _score_industry(self, industry: Optional[str], target_industry: Optional[str]) -> float:
        """Score industry alignment."""
        if not industry or not target_industry:
            return 0.5

        # Exact match
        if industry.lower() == target_industry.lower():
            return 1.0

        # Partial match (substring)
        if target_industry.lower() in industry.lower() or industry.lower() in target_industry.lower():
            return 0.8

        return 0.3  # No match

    def _score_revenue(
        self,
        annual_revenue: Optional[int],
        target_min: Optional[int],
        target_max: Optional[int],
    ) -> float:
        """Score revenue alignment."""
        if annual_revenue is None:
            return 0.5  # Neutral if unknown

        if target_min is None or target_max is None:
            return 0.5  # Can't score without target range

        # Within range = perfect
        if target_min <= annual_revenue <= target_max:
            return 1.0

        # Outside range but close = partial
        if annual_revenue < target_min:
            ratio = annual_revenue / target_min if target_min > 0 else 0.0
            return max(0.3, ratio)

        # Above range
        ratio = target_max / annual_revenue if annual_revenue > 0 else 0.0
        return max(0.3, ratio)

    def _score_location(self, company_location: Optional[str], target_location: Optional[str]) -> float:
        """Score geographic fit."""
        if not company_location or not target_location:
            return 0.5

        # Exact match
        if company_location.lower() == target_location.lower():
            return 1.0

        # Partial match (country/region)
        if target_location.lower() in company_location.lower():
            return 0.8

        return 0.4  # Different region


class OpportunityScorer:
    """
    Opportunity-based scorer.
    
    Evaluates how likely a lead is to be receptive based on:
    - Job title and seniority
    - Recent activity signals
    - Company hiring/funding signals
    """

    def __init__(
        self,
        title_weight: float = 0.35,
        seniority_weight: float = 0.25,
        signals_weight: float = 0.40,
    ):
        """
        Initialize opportunity scorer.
        
        Args:
            title_weight: Weight for job title relevance (0.0-1.0)
            seniority_weight: Weight for decision-maker seniority (0.0-1.0)
            signals_weight: Weight for buying/activity signals (0.0-1.0)
        """
        self.title_weight = title_weight
        self.seniority_weight = seniority_weight
        self.signals_weight = signals_weight

    def compute_opportunity_score(self, lead: Lead, campaign: Campaign) -> float:
        """
        Compute opportunity score (0.0-1.0) for lead.
        
        Higher score = more likely to engage + progress through pipeline.
        
        Args:
            lead: Lead domain model
            campaign: Campaign domain model
            
        Returns:
            Opportunity score (0.0-1.0)
        """
        if not lead or not campaign or not lead.enrichment_data:
            return 0.5

        enrichment = lead.enrichment_data or {}

        # Title relevance to campaign (e.g., marketing titles for marketing campaign)
        title_score = self._score_title_relevance(
            lead.role,
            getattr(campaign, "target_roles", None),
        )

        # Seniority level (decision makers > individual contributors)
        seniority_score = self._score_seniority(lead.role, enrichment.get("job_level"))

        # Recent activity and buying signals
        signals_score = self._score_opportunity_signals(enrichment)

        # Weighted combination
        opportunity_score = (
            title_score * self.title_weight
            + seniority_score * self.seniority_weight
            + signals_score * self.signals_weight
        )

        return min(1.0, max(0.0, opportunity_score))

    def _score_title_relevance(self, role: Optional[str], target_roles: Optional[List[str]]) -> float:
        """Score job title relevance."""
        if not role:
            return 0.5

        if not target_roles:
            return 0.6  # Some relevance without target list

        role_lower = role.lower()

        # Exact match
        for target_role in target_roles:
            if role_lower == target_role.lower():
                return 1.0

        # Partial match
        for target_role in target_roles:
            if target_role.lower() in role_lower or role_lower in target_role.lower():
                return 0.8

        return 0.3  # No match

    def _score_seniority(self, role: Optional[str], job_level: Optional[str]) -> float:
        """Score decision-maker seniority."""
        if not role and not job_level:
            return 0.5

        seniority_keywords = {
            "c-level": 1.0,  # CEO, CFO, CTO, etc.
            "ceo": 1.0,
            "cfo": 1.0,
            "cto": 1.0,
            "coo": 1.0,
            "executive": 0.95,
            "director": 0.90,
            "manager": 0.70,
            "lead": 0.65,
            "senior": 0.60,
            "founder": 1.0,
            "vp": 0.95,
            "president": 0.95,
            "head": 0.90,
        }

        # Check role keywords
        if role:
            role_lower = role.lower()
            for keyword, score in seniority_keywords.items():
                if keyword in role_lower:
                    return score

        # Check explicit job level
        if job_level:
            level_lower = job_level.lower()
            for keyword, score in seniority_keywords.items():
                if keyword in level_lower:
                    return score

        return 0.5  # Default individual contributor

    def _score_opportunity_signals(self, enrichment: dict) -> float:
        """Score presence of buying/activity signals."""
        score = 0.5  # Base score

        # Recent job change (strong signal)
        if enrichment.get("recent_job_change"):
            score += 0.25

        # Company recently funded (hiring, investing in growth)
        if enrichment.get("company_funded_recently"):
            score += 0.15

        # Company actively hiring (expansion signal)
        if enrichment.get("company_hiring"):
            score += 0.10

        # Recent activity on LinkedIn (engagement signal)
        if enrichment.get("recent_activity"):
            score += 0.10

        # Decision-maker role (ability to buy)
        if enrichment.get("is_decision_maker"):
            score += 0.15

        # Budget authority
        if enrichment.get("has_budget_authority"):
            score += 0.10

        return min(1.0, score)


class TierClassifier:
    """
    Lead tier classifier.
    
    Combines ICP and opportunity scores to classify leads into:
    - HOT (0.85+): Immediate outreach
    - WARM (0.65-0.84): Secondary outreach
    - COOL (0.40-0.64): Nurture/lower priority
    - COLD (<0.40): Minimal outreach
    """

    def __init__(self, icp_weight: float = 0.50, opportunity_weight: float = 0.50):
        """
        Initialize tier classifier.
        
        Args:
            icp_weight: Weight for ICP fit (0.0-1.0)
            opportunity_weight: Weight for opportunity score (0.0-1.0)
        """
        self.icp_weight = icp_weight
        self.opportunity_weight = opportunity_weight

    def classify_lead_tier(
        self,
        icp_score: float,
        opportunity_score: float,
    ) -> LeadTier:
        """
        Classify lead into opportunity tier.
        
        Args:
            icp_score: ICP fit score (0.0-1.0)
            opportunity_score: Opportunity score (0.0-1.0)
            
        Returns:
            LeadTier (HOT, WARM, COOL, or COLD)
        """
        # Combined score: weighted average
        combined_score = (
            icp_score * self.icp_weight
            + opportunity_score * self.opportunity_weight
        )

        if combined_score >= 0.85:
            return LeadTier.HOT
        elif combined_score >= 0.65:
            return LeadTier.WARM
        elif combined_score >= 0.40:
            return LeadTier.COOL
        else:
            return LeadTier.COLD


@dataclass
class ScoringMetrics:
    """Metrics for a scoring batch operation."""
    
    scored_count: int = 0
    hot_count: int = 0
    warm_count: int = 0
    cool_count: int = 0
    cold_count: int = 0
    avg_icp_score: float = 0.0
    avg_opportunity_score: float = 0.0
    avg_combined_score: float = 0.0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert metrics to dictionary."""
        return {
            "scored_count": self.scored_count,
            "hot_count": self.hot_count,
            "warm_count": self.warm_count,
            "cool_count": self.cool_count,
            "cold_count": self.cold_count,
            "avg_icp_score": round(self.avg_icp_score, 3),
            "avg_opportunity_score": round(self.avg_opportunity_score, 3),
            "avg_combined_score": round(self.avg_combined_score, 3),
            "hot_ratio": round(self.hot_count / max(1, self.scored_count), 3),
            "warm_ratio": round(self.warm_count / max(1, self.scored_count), 3),
            "duration_seconds": round(self.duration_seconds, 2),
            "errors": self.errors,
        }


def batch_score_leads(
    db: Session,
    campaign_id: int,
    max_leads: int = 100,
    icp_scorer: Optional[ICPScorer] = None,
    opportunity_scorer: Optional[OpportunityScorer] = None,
    tier_classifier: Optional[TierClassifier] = None,
) -> ScoringMetrics:
    """
    Score all unenriched leads in campaign and classify into tiers.
    
    Args:
        db: SQLAlchemy database session
        campaign_id: Campaign ID to score leads for
        max_leads: Maximum leads to score
        icp_scorer: ICPScorer instance (default: new instance)
        opportunity_scorer: OpportunityScorer instance (default: new instance)
        tier_classifier: TierClassifier instance (default: new instance)
        
    Returns:
        ScoringMetrics with scoring summary
    """
    start_time = datetime.now()
    metrics = ScoringMetrics()

    # Initialize default scorers if not provided
    if icp_scorer is None:
        icp_scorer = ICPScorer()
    if opportunity_scorer is None:
        opportunity_scorer = OpportunityScorer()
    if tier_classifier is None:
        tier_classifier = TierClassifier()

    try:
        # Fetch unenriched leads (enrichment_data exists, but not yet scored)
        leads = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.enrichment_data.isnot(None),
            LeadDB.lead_score.is_(None),  # Not yet scored
        ).limit(max_leads).all()

        if not leads:
            metrics.duration_seconds = (datetime.now() - start_time).total_seconds()
            return metrics

        # Fetch campaign for context
        campaign_db = db.query(LeadDB.__table__.columns[0]).select_from(
            db.query(LeadDB).filter(LeadDB.campaign_id == campaign_id).statement.alias()
        ).first()

        # Score each lead
        icp_scores: List[float] = []
        opportunity_scores: List[float] = []
        combined_scores: List[float] = []

        for lead_db in leads:
            try:
                # Convert DB model to domain model
                lead = Lead(
                    id=lead_db.id,
                    campaign_id=lead_db.campaign_id,
                    name=lead_db.name,
                    company=lead_db.company,
                    role=lead_db.role,
                    email=lead_db.email,
                    linkedin_url=lead_db.linkedin_url,
                    source=lead_db.source,
                    status=lead_db.status,
                    enrichment_data=lead_db.enrichment_data,
                )

                # Create minimal campaign for scoring (just needs enrichment context)
                campaign = Campaign(
                    id=campaign_id,
                    name="",
                    description="",
                    target_niche="",
                )

                # Score
                icp_score = icp_scorer.compute_icp_fit(lead, campaign)
                opportunity_score = opportunity_scorer.compute_opportunity_score(lead, campaign)
                combined_score = (icp_score + opportunity_score) / 2.0

                # Classify tier
                tier = tier_classifier.classify_lead_tier(icp_score, opportunity_score)

                # Update database
                lead_db.lead_score = combined_score
                lead_db.tags = lead_db.tags or []
                if tier.value not in lead_db.tags:
                    lead_db.tags.append(tier.value)

                # Track metrics
                icp_scores.append(icp_score)
                opportunity_scores.append(opportunity_score)
                combined_scores.append(combined_score)

                if tier == LeadTier.HOT:
                    metrics.hot_count += 1
                elif tier == LeadTier.WARM:
                    metrics.warm_count += 1
                elif tier == LeadTier.COOL:
                    metrics.cool_count += 1
                else:
                    metrics.cold_count += 1

                metrics.scored_count += 1

            except Exception as e:
                error_msg = f"Lead {lead_db.id}: {str(e)}"
                metrics.errors.append(error_msg)

        # Commit database changes
        db.commit()

        # Calculate averages
        if icp_scores:
            metrics.avg_icp_score = sum(icp_scores) / len(icp_scores)
        if opportunity_scores:
            metrics.avg_opportunity_score = sum(opportunity_scores) / len(opportunity_scores)
        if combined_scores:
            metrics.avg_combined_score = sum(combined_scores) / len(combined_scores)

    except Exception as e:
        metrics.errors.append(f"Batch error: {str(e)}")
        db.rollback()

    finally:
        metrics.duration_seconds = (datetime.now() - start_time).total_seconds()

    return metrics
