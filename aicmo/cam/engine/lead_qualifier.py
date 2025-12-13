"""
Lead Qualification Engine (Phase D-4).

Implements rule-based lead qualification with quality checks, intent signal detection,
and automatic routing to appropriate outreach sequences.

Features:
- ICP fit threshold validation
- Email quality checks (format, spam/bot detection)
- Competitor filtering
- Intent signal detection (hiring, funding, activity)
- Auto-route to appropriate sequence
- Comprehensive qualification metrics
- Atomic batch qualification
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
from enum import Enum
import re

from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, Campaign, LeadStatus
from aicmo.cam.db_models import LeadDB


class QualificationStatus(str, Enum):
    """Lead qualification outcome."""
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class RejectionReason(str, Enum):
    """Reason for lead rejection."""
    LOW_ICP_FIT = "low_icp_fit"          # ICP score < 0.7
    INVALID_EMAIL = "invalid_email"      # Bad email format
    SPAM_BOT = "spam_bot"                # Spam/bot heuristics
    COMPETITOR = "competitor"            # Competitor domain
    ROLE_ACCOUNT = "role_account"        # Info@, support@, etc.
    MULTIPLE_REASONS = "multiple_reasons"  # Multiple quality issues


@dataclass
class QualificationRules:
    """Rules for lead qualification."""
    
    icp_fit_threshold: float = 0.70  # Minimum ICP fit score
    block_competitor_domains: List[str] = field(default_factory=list)  # e.g. ["competitor.com"]
    block_role_accounts: List[str] = field(default_factory=lambda: [
        "info", "support", "sales", "noreply", "no-reply",
        "marketing", "postmaster", "root", "admin", "test",
        "hello", "hi", "general", "contact", "inquiry",
    ])
    block_free_email_domains: bool = False  # Block gmail.com, yahoo.com, etc.
    free_email_domains: List[str] = field(default_factory=lambda: [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "aol.com", "protonmail.com", "icloud.com", "mail.com",
    ])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "icp_fit_threshold": self.icp_fit_threshold,
            "block_role_accounts": self.block_role_accounts,
            "block_free_email_domains": self.block_free_email_domains,
            "block_competitor_domains": self.block_competitor_domains,
        }


class EmailQualifier:
    """Email quality validation."""
    
    # RFC 5322 simplified email regex
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Spam/bot indicators
    SPAM_KEYWORDS = {
        "bot", "spam", "mailer", "daemon", "noreply",
        "verify", "confirm", "alert", "notification",
    }

    def __init__(self, rules: Optional[QualificationRules] = None):
        """Initialize email qualifier."""
        self.rules = rules or QualificationRules()

    def is_valid_format(self, email: Optional[str]) -> bool:
        """Check if email has valid format."""
        if not email:
            return False
        return bool(self.EMAIL_PATTERN.match(email.strip().lower()))

    def is_spam_bot(self, email: str) -> bool:
        """Detect spam/bot email indicators."""
        if not email:
            return False
        
        email_lower = email.lower().strip()
        
        # Check for spam keywords
        for keyword in self.SPAM_KEYWORDS:
            if keyword in email_lower:
                return True
        
        # Check for patterns like test123, demo456, etc.
        local_part = email_lower.split('@')[0]
        if re.match(r'^(test|demo|noreply|no[-_]reply|bounce|mailer|daemon)', local_part):
            return True
        
        return False

    def is_role_account(self, email: str) -> bool:
        """Detect if email is a role account (info@, support@, etc.)."""
        if not email:
            return False
        
        local_part = email.lower().split('@')[0]
        
        # Check against blocked role accounts
        for role in self.rules.block_role_accounts:
            if local_part == role or local_part.startswith(role + '.') or local_part.startswith(role + '_'):
                return True
        
        return False

    def is_free_email(self, email: str) -> bool:
        """Check if email is from free provider."""
        if not email:
            return False
        
        domain = email.lower().split('@')[1]
        return domain in self.rules.free_email_domains

    def is_competitor_domain(self, email: str) -> bool:
        """Check if email is from competitor domain."""
        if not email or not self.rules.block_competitor_domains:
            return False
        
        domain = email.lower().split('@')[1]
        return domain in self.rules.block_competitor_domains

    def check_email_quality(self, email: Optional[str]) -> Tuple[bool, Optional[RejectionReason]]:
        """
        Comprehensive email quality check.
        
        Returns:
            (is_valid, rejection_reason)
        """
        if not email:
            return False, RejectionReason.INVALID_EMAIL
        
        # Check format
        if not self.is_valid_format(email):
            return False, RejectionReason.INVALID_EMAIL
        
        reasons = []
        
        # Check for spam/bot
        if self.is_spam_bot(email):
            reasons.append(RejectionReason.SPAM_BOT)
        
        # Check for role account
        if self.is_role_account(email):
            reasons.append(RejectionReason.ROLE_ACCOUNT)
        
        # Check for competitor
        if self.is_competitor_domain(email):
            reasons.append(RejectionReason.COMPETITOR)
        
        # Check for free email if blocked
        if self.rules.block_free_email_domains and self.is_free_email(email):
            return False, RejectionReason.INVALID_EMAIL
        
        # Return first reason or multiple
        if reasons:
            return False, reasons[0] if len(reasons) == 1 else RejectionReason.MULTIPLE_REASONS
        
        return True, None


class IntentDetector:
    """Detect buying intent and activity signals."""

    def detect_intent(self, lead: Lead) -> bool:
        """
        Detect if lead shows buying intent or activity signals.
        
        Returns True if lead shows strong intent signals.
        """
        if not lead.enrichment_data:
            return False
        
        enrichment = lead.enrichment_data
        
        # Strong intent signals
        strong_signals = 0
        
        if enrichment.get("recent_job_change"):
            strong_signals += 1  # Just hired person (likely has budget/authority)
        
        if enrichment.get("company_funded_recently"):
            strong_signals += 1  # Company expanding (hiring, investing)
        
        if enrichment.get("company_hiring"):
            strong_signals += 1  # Active hiring (growth mode)
        
        if enrichment.get("recent_activity"):
            strong_signals += 1  # Recently active on LinkedIn
        
        # At least 2 strong signals = intent detected
        return strong_signals >= 2

    def get_intent_score(self, lead: Lead) -> float:
        """
        Calculate intent score (0.0-1.0).
        
        Higher = more likely to engage based on signals.
        """
        if not lead.enrichment_data:
            return 0.0
        
        enrichment = lead.enrichment_data
        score = 0.0
        
        # Each signal adds points
        if enrichment.get("recent_job_change"):
            score += 0.25
        
        if enrichment.get("company_funded_recently"):
            score += 0.20
        
        if enrichment.get("company_hiring"):
            score += 0.20
        
        if enrichment.get("recent_activity"):
            score += 0.15
        
        if enrichment.get("is_decision_maker"):
            score += 0.10
        
        if enrichment.get("has_budget_authority"):
            score += 0.10
        
        return min(1.0, score)


class LeadQualifier:
    """
    Main lead qualification engine.
    
    Evaluates leads against rules and marks as QUALIFIED/REJECTED.
    """

    def __init__(
        self,
        rules: Optional[QualificationRules] = None,
        email_qualifier: Optional[EmailQualifier] = None,
        intent_detector: Optional[IntentDetector] = None,
    ):
        """
        Initialize lead qualifier.
        
        Args:
            rules: Qualification rules
            email_qualifier: Email validation component
            intent_detector: Intent signal detection
        """
        self.rules = rules or QualificationRules()
        self.email_qualifier = email_qualifier or EmailQualifier(self.rules)
        self.intent_detector = intent_detector or IntentDetector()

    def auto_qualify_lead(
        self,
        lead: Lead,
    ) -> Tuple[QualificationStatus, Optional[RejectionReason], str]:
        """
        Auto-qualify a single lead.
        
        Args:
            lead: Lead to qualify
            
        Returns:
            (status, rejection_reason, reasoning)
        """
        reasoning_parts = []
        
        # Check 1: ICP fit threshold
        if not lead.lead_score or lead.lead_score < self.rules.icp_fit_threshold:
            reason = f"ICP fit score {lead.lead_score:.2f} below threshold {self.rules.icp_fit_threshold}"
            reasoning_parts.append(reason)
            return (
                QualificationStatus.REJECTED,
                RejectionReason.LOW_ICP_FIT,
                reason
            )
        
        reasoning_parts.append(f"✓ ICP fit score {lead.lead_score:.2f}")
        
        # Check 2: Email quality
        if lead.email:
            is_valid, rejection_reason = self.email_qualifier.check_email_quality(lead.email)
            if not is_valid:
                reason = f"Email quality check failed: {rejection_reason.value if rejection_reason else 'unknown'}"
                return (
                    QualificationStatus.REJECTED,
                    rejection_reason,
                    reason
                )
            reasoning_parts.append(f"✓ Email quality check passed")
        else:
            reasoning_parts.append("⚠ No email provided")
        
        # Check 3: Intent detection (recommend for manual review if no strong intent)
        intent_score = self.intent_detector.get_intent_score(lead)
        reasoning_parts.append(f"✓ Intent score: {intent_score:.2f}")
        
        if intent_score < 0.2 and not lead.enrichment_data.get("is_decision_maker"):
            # Low intent and not a decision maker - flag for review
            return (
                QualificationStatus.MANUAL_REVIEW,
                None,
                "Low intent signals but ICP fit passes; recommend review"
            )
        
        # All checks passed
        reasoning_parts.append("✓ All qualification checks passed")
        return (
            QualificationStatus.QUALIFIED,
            None,
            " | ".join(reasoning_parts)
        )

    def batch_qualify_leads(
        self,
        db: Session,
        campaign_id: int,
        max_leads: int = 100,
    ) -> "QualificationMetrics":
        """
        Qualify all scored, unqualified leads in campaign.
        
        Args:
            db: SQLAlchemy session
            campaign_id: Campaign ID
            max_leads: Maximum leads to process
            
        Returns:
            Metrics summary
        """
        start_time = datetime.now()
        metrics = QualificationMetrics()
        
        try:
            # Fetch scored leads without qualification
            leads = db.query(LeadDB).filter(
                LeadDB.campaign_id == campaign_id,
                LeadDB.lead_score.isnot(None),  # Must be scored
                LeadDB.status.in_([LeadStatus.NEW, LeadStatus.ENRICHED]),  # Not yet qualified
            ).limit(max_leads).all()
            
            if not leads:
                metrics.duration_seconds = (datetime.now() - start_time).total_seconds()
                return metrics
            
            # Process each lead
            for lead_db in leads:
                try:
                    # Convert to domain model
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
                        lead_score=lead_db.lead_score,
                        tags=lead_db.tags or [],
                        enrichment_data=lead_db.enrichment_data,
                    )
                    
                    # Qualify
                    status, reason, reasoning = self.auto_qualify_lead(lead)
                    
                    # Update database
                    if status == QualificationStatus.QUALIFIED:
                        lead_db.status = LeadStatus.QUALIFIED
                        metrics.qualified_count += 1
                    elif status == QualificationStatus.REJECTED:
                        lead_db.status = LeadStatus.LOST
                        metrics.rejected_count += 1
                    else:
                        metrics.manual_review_count += 1
                    
                    # Store reasoning in notes
                    if lead_db.notes:
                        lead_db.notes += f"\n[QUALIFIED] {reasoning}"
                    else:
                        lead_db.notes = f"[QUALIFIED] {reasoning}"
                    
                    metrics.processed_count += 1
                    
                except Exception as e:
                    error_msg = f"Lead {lead_db.id}: {str(e)}"
                    metrics.errors.append(error_msg)
            
            # Commit changes
            db.commit()
            
        except Exception as e:
            metrics.errors.append(f"Batch error: {str(e)}")
            db.rollback()
        
        finally:
            metrics.duration_seconds = (datetime.now() - start_time).total_seconds()
        
        return metrics


@dataclass
class QualificationMetrics:
    """Metrics for a qualification batch operation."""
    
    processed_count: int = 0
    qualified_count: int = 0
    rejected_count: int = 0
    manual_review_count: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        total = self.processed_count if self.processed_count > 0 else 1
        return {
            "processed_count": self.processed_count,
            "qualified_count": self.qualified_count,
            "rejected_count": self.rejected_count,
            "manual_review_count": self.manual_review_count,
            "qualified_ratio": round(self.qualified_count / total, 3),
            "rejected_ratio": round(self.rejected_count / total, 3),
            "manual_review_ratio": round(self.manual_review_count / total, 3),
            "duration_seconds": round(self.duration_seconds, 2),
            "errors": self.errors,
        }
