"""
Lead Nurture Engine - Phase 6

Handles email sequence execution, engagement tracking, and lead status updates
based on email interactions (opens, clicks, replies). Manages the complete
nurture workflow for leads routed to different sequences (HOT/WARM/COOL/COLD).

Architecture:
- EmailTemplate: Template rendering with personalization
- EngagementTracker: Track email opens, clicks, replies
- NurtureScheduler: Calculate when to send next email in sequence
- NurtureOrchestrator: Main orchestration engine
- NurtureMetrics: Batch operation metrics

Integration:
- Consumes routed leads (status=ROUTED, routing_sequence set)
- Sends emails from ContentSequence (Phase 5)
- Tracks engagement metrics
- Updates lead status based on engagement
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Tuple
from uuid import uuid4

from sqlalchemy import and_
from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadStatus, LeadSource
from aicmo.cam.db_models import LeadDB
from aicmo.cam.engine.lead_router import ContentSequenceType


logger = logging.getLogger(__name__)


class EngagementEvent(Enum):
    """Types of email engagement events."""
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


@dataclass
class EmailTemplate:
    """Email template with personalization support.
    
    Attributes:
        sequence_type: Which sequence this email belongs to
        email_number: Position in sequence (1-indexed)
        subject: Email subject with {placeholders}
        body: Email body with {placeholders}
        cta_link: Call-to-action URL
    """
    sequence_type: ContentSequenceType
    email_number: int
    subject: str
    body: str
    cta_link: Optional[str] = None
    
    def render(self, lead: Lead) -> Tuple[str, str]:
        """Render template with lead data substitution.
        
        Args:
            lead: Lead to personalize for
            
        Returns:
            Tuple of (rendered_subject, rendered_body)
        """
        context = {
            "first_name": lead.first_name or "there",
            "company": lead.company or "your company",
            "title": lead.title or "professional",
        }
        
        try:
            subject = self.subject.format(**context)
            body = self.body.format(**context)
            return subject, body
        except KeyError as e:
            logger.warning(f"Missing template key {e} for lead {lead.id}")
            return self.subject, self.body


@dataclass
class EngagementRecord:
    """Record of an engagement event.
    
    Attributes:
        event_type: Type of engagement (opened, clicked, replied, etc.)
        timestamp: When the event occurred
        email_number: Which email in sequence triggered event
        metadata: Additional event data (link clicked, reply content, etc.)
    """
    event_type: EngagementEvent
    timestamp: datetime
    email_number: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class EngagementMetrics:
    """Metrics for engagement summary.
    
    Attributes:
        total_sent: Total emails sent
        opened_count: Emails opened
        clicked_count: Emails with clicks
        replied_count: Email replies
        bounced_count: Bounced emails
        unsubscribed_count: Unsubscribe events
    """
    total_sent: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    replied_count: int = 0
    bounced_count: int = 0
    unsubscribed_count: int = 0
    
    @property
    def open_rate(self) -> float:
        """Calculate open rate (%)."""
        if self.total_sent == 0:
            return 0.0
        return (self.opened_count / self.total_sent) * 100
    
    @property
    def click_rate(self) -> float:
        """Calculate click rate (%)."""
        if self.opened_count == 0:
            return 0.0
        return (self.clicked_count / self.opened_count) * 100
    
    @property
    def reply_rate(self) -> float:
        """Calculate reply rate (%)."""
        if self.total_sent == 0:
            return 0.0
        return (self.replied_count / self.total_sent) * 100


@dataclass
class EmailSendResult:
    """Result of sending a single email.
    
    Attributes:
        lead_id: Lead email was sent to
        sequence_type: Which sequence this belongs to
        email_number: Position in sequence
        message_id: Unique email identifier
        success: Whether send succeeded
        error: Error message if send failed
        sent_at: When email was sent
    """
    lead_id: str
    sequence_type: ContentSequenceType
    email_number: int
    message_id: str
    success: bool
    error: Optional[str] = None
    sent_at: Optional[datetime] = None


class NurtureScheduler:
    """Calculates when to send next email in a sequence."""
    
    # Inter-email delays (hours) - configurable per sequence type
    SEQUENCE_DELAYS = {
        ContentSequenceType.AGGRESSIVE_CLOSE: [0, 2, 5],  # Days: 0, 2, 5
        ContentSequenceType.REGULAR_NURTURE: [0, 3, 7, 10],  # Days: 0, 3, 7, 10
        ContentSequenceType.LONG_TERM_NURTURE: [0, 5, 10, 15, 20, 25],  # Days: 0, 5, 10, ...
        ContentSequenceType.COLD_OUTREACH: [0, 7, 14, 21, 28, 35, 42, 49],  # Days: weekly
    }
    
    @staticmethod
    def get_next_send_time(
        lead: Lead,
        sequence_type: ContentSequenceType,
        current_email_index: int,
    ) -> datetime:
        """Calculate when to send next email.
        
        Args:
            lead: Lead being nurtured
            sequence_type: Type of sequence
            current_email_index: Index of email just sent (0-indexed)
            
        Returns:
            Datetime for next send
        """
        delays = NurtureScheduler.SEQUENCE_DELAYS[sequence_type]
        
        # If beyond sequence, no next send
        if current_email_index >= len(delays) - 1:
            return None
        
        next_index = current_email_index + 1
        next_delay_days = delays[next_index]
        
        # Calculate from sequence start
        if lead.sequence_start_at:
            return lead.sequence_start_at + timedelta(days=next_delay_days)
        
        # Default to now + delay
        return datetime.utcnow() + timedelta(days=next_delay_days)
    
    @staticmethod
    def should_send_next_email(
        lead: Lead,
        sequence_type: ContentSequenceType,
        current_email_index: int,
    ) -> bool:
        """Check if it's time to send next email.
        
        Args:
            lead: Lead being nurtured
            sequence_type: Type of sequence
            current_email_index: Index of last sent email (0-indexed)
            
        Returns:
            True if next send time has arrived
        """
        delays = NurtureScheduler.SEQUENCE_DELAYS[sequence_type]
        
        if current_email_index >= len(delays) - 1:
            return False
        
        next_send = NurtureScheduler.get_next_send_time(
            lead, sequence_type, current_email_index
        )
        
        if next_send is None:
            return False
        
        return datetime.utcnow() >= next_send


@dataclass
class NurtureDecision:
    """Decision for nurturing a lead.
    
    Attributes:
        lead_id: Lead to nurture
        should_send: Whether to send email
        reason: Why we should/shouldn't send
        next_email_number: Which email to send (1-indexed)
        template: EmailTemplate if should_send
    """
    lead_id: str
    should_send: bool
    reason: str
    next_email_number: Optional[int] = None
    template: Optional[EmailTemplate] = None


class NurtureOrchestrator:
    """Main nurture engine - orchestrates sequence execution.
    
    Handles:
    - Determining which leads need nurturing
    - Scheduling emails at appropriate times
    - Sending emails from templates
    - Tracking engagement
    - Updating lead status based on engagement
    """
    
    def __init__(self, session: Session):
        """Initialize orchestrator.
        
        Args:
            session: SQLAlchemy session for database access
        """
        self.session = session
        self._engagement_tracker: Dict[str, List[EngagementRecord]] = {}
    
    def get_leads_to_nurture(self) -> List[Lead]:
        """Get all leads that need nurturing.
        
        Returns:
            List of leads in ROUTED status that haven't finished sequences
        """
        leads_db = self.session.query(LeadDB).filter(
            and_(
                LeadDB.status == LeadStatus.ROUTED.value,
                LeadDB.routing_sequence.isnot(None),
                LeadDB.sequence_start_at.isnot(None),
            )
        ).all()
        
        leads = []
        for lead_db in leads_db:
            # Convert database model to domain model
            lead = Lead(
                id=lead_db.id,
                campaign_id=lead_db.campaign_id,
                name=lead_db.name,
                first_name=lead_db.first_name,
                title=lead_db.title,
                email=lead_db.email,
                company=lead_db.company,
                role=lead_db.role,
                source=LeadSource(lead_db.source) if lead_db.source else LeadSource.CSV,
                status=LeadStatus(lead_db.status) if lead_db.status else LeadStatus.NEW,
                lead_score=lead_db.lead_score,
                routing_sequence=lead_db.routing_sequence,
                sequence_start_at=lead_db.sequence_start_at,
            )
            leads.append(lead)
        
        return leads
    
    def evaluate_lead_nurture(
        self,
        lead: Lead,
    ) -> NurtureDecision:
        """Evaluate if lead should receive next email.
        
        Args:
            lead: Lead to evaluate
            
        Returns:
            NurtureDecision with send recommendation
        """
        # Map routing_sequence string back to enum
        try:
            sequence_type = ContentSequenceType(lead.routing_sequence)
        except (ValueError, AttributeError):
            return NurtureDecision(
                lead_id=lead.id,
                should_send=False,
                reason=f"Invalid routing sequence: {lead.routing_sequence}",
            )
        
        # Get engagement tracking for lead
        engagement = self._engagement_tracker.get(lead.id, [])
        
        # Current email index is number of emails already sent
        sent_count = len(engagement)
        
        # Check if should send next email
        should_send = NurtureScheduler.should_send_next_email(
            lead=lead,
            sequence_type=sequence_type,
            current_email_index=sent_count - 1 if sent_count > 0 else 0,
        )
        
        if not should_send:
            return NurtureDecision(
                lead_id=lead.id,
                should_send=False,
                reason="Not yet time for next email",
            )
        
        # Get next email template
        template = self._get_email_template(sequence_type, sent_count + 1)
        
        if template is None:
            return NurtureDecision(
                lead_id=lead.id,
                should_send=False,
                reason="Sequence complete",
            )
        
        return NurtureDecision(
            lead_id=lead.id,
            should_send=True,
            reason="Ready for next email",
            next_email_number=sent_count + 1,
            template=template,
        )
    
    def send_email(
        self,
        lead: Lead,
        template: EmailTemplate,
        email_number: int,
    ) -> EmailSendResult:
        """Send email to a lead.
        
        Args:
            lead: Lead to send to
            template: Email template
            email_number: Position in sequence (1-indexed)
            
        Returns:
            EmailSendResult with send status
        """
        try:
            # Render template
            subject, body = template.render(lead)
            
            # Generate message ID
            message_id = str(uuid4())
            
            # In production, would call email provider API here
            # For now, simulate successful send
            logger.info(
                f"Sending email {email_number} to {lead.email}: {subject}"
            )
            
            # Track engagement for this lead
            if lead.id not in self._engagement_tracker:
                self._engagement_tracker[lead.id] = []
            
            # Record that email was sent (will be updated as opens/clicks occur)
            self._engagement_tracker[lead.id].append(
                EngagementRecord(
                    event_type=EngagementEvent.OPENED,  # Placeholder
                    timestamp=datetime.utcnow(),
                    email_number=email_number,
                    metadata={"message_id": message_id},
                )
            )
            
            return EmailSendResult(
                lead_id=lead.id,
                sequence_type=template.sequence_type,
                email_number=email_number,
                message_id=message_id,
                success=True,
                sent_at=datetime.utcnow(),
            )
        
        except Exception as e:
            logger.error(f"Failed to send email to {lead.email}: {str(e)}")
            return EmailSendResult(
                lead_id=lead.id,
                sequence_type=template.sequence_type,
                email_number=email_number,
                message_id=None,
                success=False,
                error=str(e),
            )
    
    def record_engagement(
        self,
        lead_id: str,
        event_type: EngagementEvent,
        email_number: int,
        metadata: Dict = None,
    ) -> None:
        """Record engagement event for a lead.
        
        Args:
            lead_id: Lead that engaged
            event_type: Type of engagement
            email_number: Which email triggered event
            metadata: Additional event data
        """
        if lead_id not in self._engagement_tracker:
            self._engagement_tracker[lead_id] = []
        
        self._engagement_tracker[lead_id].append(
            EngagementRecord(
                event_type=event_type,
                timestamp=datetime.utcnow(),
                email_number=email_number,
                metadata=metadata or {},
            )
        )
    
    def get_engagement_metrics(self, lead_id: str) -> EngagementMetrics:
        """Get engagement metrics for a lead.
        
        Args:
            lead_id: Lead to get metrics for
            
        Returns:
            EngagementMetrics with open/click/reply rates
        """
        engagement = self._engagement_tracker.get(lead_id, [])
        
        metrics = EngagementMetrics(total_sent=len(engagement))
        
        for record in engagement:
            if record.event_type == EngagementEvent.OPENED:
                metrics.opened_count += 1
            elif record.event_type == EngagementEvent.CLICKED:
                metrics.clicked_count += 1
            elif record.event_type == EngagementEvent.REPLIED:
                metrics.replied_count += 1
            elif record.event_type == EngagementEvent.BOUNCED:
                metrics.bounced_count += 1
            elif record.event_type == EngagementEvent.UNSUBSCRIBED:
                metrics.unsubscribed_count += 1
        
        return metrics
    
    def update_lead_status(
        self,
        lead_id: str,
        session: Session,
    ) -> None:
        """Update lead status based on engagement.
        
        Args:
            lead_id: Lead to update
            session: Database session
        """
        engagement = self._engagement_tracker.get(lead_id, [])
        
        if not engagement:
            return
        
        # Check for specific engagement events
        has_reply = any(
            r.event_type == EngagementEvent.REPLIED for r in engagement
        )
        has_bounce = any(
            r.event_type == EngagementEvent.BOUNCED for r in engagement
        )
        has_unsubscribe = any(
            r.event_type == EngagementEvent.UNSUBSCRIBED for r in engagement
        )
        
        # Update lead in database
        lead_db = session.query(LeadDB).filter(LeadDB.id == lead_id).first()
        
        if not lead_db:
            return
        
        if has_reply:
            lead_db.status = LeadStatus.CONTACTED.value
            lead_db.engagement_notes = "Lead replied to email"
            logger.info(f"Lead {lead_id} moved to CONTACTED after reply")
        
        elif has_bounce:
            lead_db.status = LeadStatus.INVALID.value
            lead_db.engagement_notes = "Email bounced"
            logger.info(f"Lead {lead_id} marked INVALID after bounce")
        
        elif has_unsubscribe:
            lead_db.status = LeadStatus.LOST.value
            lead_db.engagement_notes = "Lead unsubscribed"
            logger.info(f"Lead {lead_id} marked LOST after unsubscribe")
        
        session.commit()
    
    @staticmethod
    def _get_email_template(
        sequence_type: ContentSequenceType,
        email_number: int,
    ) -> Optional[EmailTemplate]:
        """Get predefined email template for sequence.
        
        Args:
            sequence_type: Type of sequence
            email_number: Position in sequence (1-indexed)
            
        Returns:
            EmailTemplate or None if sequence complete
        """
        templates = {
            ContentSequenceType.AGGRESSIVE_CLOSE: [
                EmailTemplate(
                    sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
                    email_number=1,
                    subject="Quick conversation about {company}?",
                    body="Hi {first_name},\n\nI've been researching {company} and think we might be able to help.\n\nWould you be open to a 15-minute call?\n\nBest",
                    cta_link="https://calendly.com/schedule",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
                    email_number=2,
                    subject="Still interested in a brief chat?",
                    body="Hi {first_name},\n\nJust following up on my previous message. We've helped similar companies cut time-to-value in half.\n\nCould we find 15 minutes this week?\n\nBest",
                    cta_link="https://calendly.com/schedule",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
                    email_number=3,
                    subject="Final check-in: Are you open to one quick call?",
                    body="Hi {first_name},\n\nThis is my last attempt to reach you. If you're not interested, no worries—I'll stop here.\n\nBut if there's any chance you'd like to explore this, I'm here.\n\nBest",
                    cta_link="https://calendly.com/schedule",
                ),
            ],
            ContentSequenceType.REGULAR_NURTURE: [
                EmailTemplate(
                    sequence_type=ContentSequenceType.REGULAR_NURTURE,
                    email_number=1,
                    subject="Interesting article about your industry",
                    body="Hi {first_name},\n\nI came across an article that might be relevant to {company}. Thought you'd find it valuable.\n\nBest",
                    cta_link="https://blog.example.com/industry-trends",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.REGULAR_NURTURE,
                    email_number=2,
                    subject="Quick idea for {company}",
                    body="Hi {first_name},\n\nBased on what I know about {company}, I think this approach could help.\n\nHappy to share more details if interested.\n\nBest",
                    cta_link="https://example.com/solutions",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.REGULAR_NURTURE,
                    email_number=3,
                    subject="How similar companies are solving this",
                    body="Hi {first_name},\n\nWanted to share how other companies in your industry are addressing similar challenges.\n\nLet me know if this resonates.\n\nBest",
                    cta_link="https://example.com/case-studies",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.REGULAR_NURTURE,
                    email_number=4,
                    subject="Would a quick conversation help?",
                    body="Hi {first_name},\n\nBased on our interactions, I think a brief call could be valuable.\n\nNo pressure—just wanted to offer.\n\nBest",
                    cta_link="https://calendly.com/schedule",
                ),
            ],
            ContentSequenceType.LONG_TERM_NURTURE: [
                EmailTemplate(
                    sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
                    email_number=1,
                    subject="Valuable resource for {title}s",
                    body="Hi {first_name},\n\nThought this resource would be helpful for your role.\n\nBest",
                    cta_link="https://example.com/resources",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
                    email_number=2,
                    subject="Latest industry trends",
                    body="Hi {first_name},\n\nSharing the latest trends in your industry.\n\nBest",
                    cta_link="https://blog.example.com/trends",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
                    email_number=3,
                    subject="Success story from your industry",
                    body="Hi {first_name},\n\nThought you might find this case study interesting.\n\nBest",
                    cta_link="https://example.com/case-studies",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
                    email_number=4,
                    subject="Another valuable resource",
                    body="Hi {first_name},\n\nContinuing to share resources I think you'll value.\n\nBest",
                    cta_link="https://example.com/resources",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
                    email_number=5,
                    subject="Industry benchmark report",
                    body="Hi {first_name},\n\nSharing a comprehensive benchmark report for {company}s.\n\nBest",
                    cta_link="https://example.com/benchmarks",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.LONG_TERM_NURTURE,
                    email_number=6,
                    subject="Whenever you're ready to chat",
                    body="Hi {first_name},\n\nI've shared a lot of value over time. Whenever {company} is ready to explore, I'm here.\n\nBest",
                    cta_link="https://calendly.com/schedule",
                ),
            ],
            ContentSequenceType.COLD_OUTREACH: [
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=1,
                    subject="Valuable resource for your industry",
                    body="Hi {first_name},\n\nThought this guide on industry trends might be useful.\n\nBest",
                    cta_link="https://example.com/guide",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=2,
                    subject="Industry trends whitepaper",
                    body="Hi {first_name},\n\nSharing a comprehensive whitepaper on industry trends.\n\nBest",
                    cta_link="https://example.com/whitepaper",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=3,
                    subject="Education resource for {title}s",
                    body="Hi {first_name},\n\nBased on your role, thought this education series could help.\n\nBest",
                    cta_link="https://example.com/education",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=4,
                    subject="Case study: Similar company success",
                    body="Hi {first_name},\n\nThought this case study about a similar company could be interesting.\n\nBest",
                    cta_link="https://example.com/case-studies",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=5,
                    subject="Monthly industry insights",
                    body="Hi {first_name},\n\nSharing this month's industry insights.\n\nBest",
                    cta_link="https://blog.example.com/insights",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=6,
                    subject="Product positioning guide",
                    body="Hi {first_name},\n\nSharing how leading companies are positioning in the market.\n\nBest",
                    cta_link="https://example.com/positioning",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=7,
                    subject="Technology landscape overview",
                    body="Hi {first_name},\n\nSharing an overview of the technology landscape.\n\nBest",
                    cta_link="https://example.com/tech-landscape",
                ),
                EmailTemplate(
                    sequence_type=ContentSequenceType.COLD_OUTREACH,
                    email_number=8,
                    subject="Final resource and next steps",
                    body="Hi {first_name},\n\nSharing one final resource. When you're ready to explore, I'm here.\n\nBest",
                    cta_link="https://calendly.com/schedule",
                ),
            ],
        }
        
        sequence_templates = templates.get(sequence_type, [])
        
        # Return template if it exists (1-indexed to 0-indexed conversion)
        if email_number <= len(sequence_templates):
            return sequence_templates[email_number - 1]
        
        return None


@dataclass
class NurtureMetrics:
    """Metrics for batch nurture operations.
    
    Attributes:
        total_leads: Total leads processed
        emails_sent: Total emails sent
        opens: Total opens
        clicks: Total clicks
        replies: Total replies
        bounces: Total bounces
        unsubscribes: Total unsubscribes
        errors: Total errors
        duration_seconds: Time to process batch
    """
    total_leads: int = 0
    emails_sent: int = 0
    opens: int = 0
    clicks: int = 0
    replies: int = 0
    bounces: int = 0
    unsubscribes: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (%)."""
        if self.total_leads == 0:
            return 0.0
        return ((self.total_leads - self.errors) / self.total_leads) * 100
    
    @property
    def avg_emails_per_lead(self) -> float:
        """Calculate average emails per lead."""
        if self.total_leads == 0:
            return 0.0
        return self.emails_sent / self.total_leads
    
    @property
    def overall_open_rate(self) -> float:
        """Calculate overall open rate (%)."""
        if self.emails_sent == 0:
            return 0.0
        return (self.opens / self.emails_sent) * 100
    
    @property
    def overall_click_rate(self) -> float:
        """Calculate overall click rate (%)."""
        if self.opens == 0:
            return 0.0
        return (self.clicks / self.opens) * 100
    
    @property
    def overall_reply_rate(self) -> float:
        """Calculate overall reply rate (%)."""
        if self.emails_sent == 0:
            return 0.0
        return (self.replies / self.emails_sent) * 100
