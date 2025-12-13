"""
Test suite for Phase 6: Lead Nurture Engine

Tests coverage:
- EmailTemplate rendering with personalization
- EngagementEvent tracking
- NurtureScheduler send timing calculations
- NurtureOrchestrator main nurture logic
- NurtureMetrics batch operations
- Full end-to-end nurture workflows
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from aicmo.cam.domain import Lead, LeadStatus, LeadSource
from aicmo.cam.engine.lead_router import ContentSequenceType
from aicmo.cam.engine.lead_nurture import (
    EmailTemplate,
    EngagementEvent,
    EngagementRecord,
    EngagementMetrics,
    EmailSendResult,
    NurtureScheduler,
    NurtureDecision,
    NurtureOrchestrator,
    NurtureMetrics,
)


class TestEmailTemplate:
    """Test email template rendering and personalization."""
    
    def test_template_creation(self):
        """Test creating email template."""
        template = EmailTemplate(
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            email_number=1,
            subject="Hello {first_name}",
            body="Hi {first_name}, company is {company}",
            cta_link="https://example.com",
        )
        
        assert template.sequence_type == ContentSequenceType.AGGRESSIVE_CLOSE
        assert template.email_number == 1
        assert template.cta_link == "https://example.com"
    
    def test_render_with_all_fields(self):
        """Test rendering template with all personalization fields."""
        template = EmailTemplate(
            sequence_type=ContentSequenceType.REGULAR_NURTURE,
            email_number=1,
            subject="Hi {first_name} from {company}",
            body="Dear {first_name},\n\nYour company is {company}. Your title is {title}.",
        )
        
        lead = Lead(
            name="John Smith",
            first_name="John",
            company="Acme Corp",
            title="VP Sales",
            email="john@acme.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
        )
        
        subject, body = template.render(lead)
        
        assert subject == "Hi John from Acme Corp"
        assert "John" in body
        assert "Acme Corp" in body
        assert "VP Sales" in body
    
    def test_render_with_missing_fields(self):
        """Test rendering template handles missing lead fields."""
        template = EmailTemplate(
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            email_number=1,
            subject="Hello {first_name}",
            body="You work at {company}",
        )
        
        lead = Lead(
            name="Unknown",
            first_name=None,
            company=None,
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
        )
        
        subject, body = template.render(lead)
        
        assert "there" in subject
        assert "your company" in body


class TestEngagementMetrics:
    """Test engagement metrics calculations."""
    
    def test_empty_metrics(self):
        """Test metrics with no engagement."""
        metrics = EngagementMetrics()
        
        assert metrics.total_sent == 0
        assert metrics.open_rate == 0.0
        assert metrics.click_rate == 0.0
        assert metrics.reply_rate == 0.0
    
    def test_open_rate_calculation(self):
        """Test open rate calculation."""
        metrics = EngagementMetrics(
            total_sent=10,
            opened_count=5,
        )
        
        assert metrics.open_rate == 50.0
    
    def test_click_rate_calculation(self):
        """Test click rate calculation."""
        metrics = EngagementMetrics(
            total_sent=10,
            opened_count=5,
            clicked_count=2,
        )
        
        assert metrics.click_rate == 40.0
    
    def test_reply_rate_calculation(self):
        """Test reply rate calculation."""
        metrics = EngagementMetrics(
            total_sent=20,
            replied_count=3,
        )
        
        assert metrics.reply_rate == 15.0


class TestNurtureScheduler:
    """Test email scheduling calculations."""
    
    def test_aggressive_close_delays(self):
        """Test aggressive close sequence delays."""
        delays = NurtureScheduler.SEQUENCE_DELAYS[ContentSequenceType.AGGRESSIVE_CLOSE]
        
        assert delays[0] == 0
        assert delays[1] == 2
        assert delays[2] == 5
    
    def test_regular_nurture_delays(self):
        """Test regular nurture sequence delays."""
        delays = NurtureScheduler.SEQUENCE_DELAYS[ContentSequenceType.REGULAR_NURTURE]
        
        assert delays[0] == 0
        assert delays[1] == 3
        assert delays[2] == 7
        assert delays[3] == 10
    
    def test_get_next_send_time(self):
        """Test calculating next send time."""
        start_time = datetime.utcnow()
        
        lead = Lead(
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            sequence_start_at=start_time,
        )
        
        next_time = NurtureScheduler.get_next_send_time(
            lead=lead,
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            current_email_index=0,
        )
        
        assert next_time > start_time
        assert (next_time - start_time).days == 2
    
    def test_should_send_next_email_false_when_early(self):
        """Test should_send returns False when not yet time."""
        future_start = datetime.utcnow() + timedelta(days=10)
        
        lead = Lead(
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            sequence_start_at=future_start,
        )
        
        should_send = NurtureScheduler.should_send_next_email(
            lead=lead,
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            current_email_index=0,
        )
        
        assert should_send is False
    
    def test_should_send_next_email_true_when_ready(self):
        """Test should_send returns True when time arrived."""
        past_start = datetime.utcnow() - timedelta(days=3)
        
        lead = Lead(
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            sequence_start_at=past_start,
        )
        
        should_send = NurtureScheduler.should_send_next_email(
            lead=lead,
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            current_email_index=0,
        )
        
        assert should_send is True
    
    def test_should_send_false_when_sequence_complete(self):
        """Test should_send returns False when sequence finished."""
        lead = Lead(
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            sequence_start_at=datetime.utcnow(),
        )
        
        should_send = NurtureScheduler.should_send_next_email(
            lead=lead,
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            current_email_index=2,
        )
        
        assert should_send is False


class TestNurtureOrchestrator:
    """Test main nurture orchestrator."""
    
    def test_orchestrator_creation(self):
        """Test creating orchestrator."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        assert orchestrator.session == session
        assert orchestrator._engagement_tracker == {}
    
    def test_evaluate_lead_nurture_valid_sequence(self):
        """Test evaluating lead with valid sequence."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        lead = Lead(
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            routing_sequence="aggressive_close",
            sequence_start_at=datetime.utcnow() - timedelta(days=3),
        )
        
        decision = orchestrator.evaluate_lead_nurture(lead)
        
        assert decision.lead_id == lead.id
        assert decision.should_send is True
        assert decision.next_email_number == 1
    
    def test_evaluate_lead_nurture_invalid_sequence(self):
        """Test evaluating lead with invalid sequence."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        lead = Lead(
            name="Test Lead",
            email="test@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            routing_sequence="invalid_sequence",
        )
        
        decision = orchestrator.evaluate_lead_nurture(lead)
        
        assert decision.should_send is False
        assert "Invalid routing sequence" in decision.reason
    
    def test_send_email_success(self):
        """Test sending email successfully."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        template = EmailTemplate(
            sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
            email_number=1,
            subject="Hello {first_name}",
            body="Hi {first_name}",
        )
        
        lead = Lead(
            name="John Smith",
            first_name="John",
            email="john@example.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
        )
        
        result = orchestrator.send_email(lead, template, email_number=1)
        
        assert result.success is True
        assert result.lead_id == lead.id
        assert result.sent_at is not None
        assert result.message_id is not None
    
    def test_record_engagement(self):
        """Test recording engagement event."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        lead_id = 1
        orchestrator.record_engagement(
            lead_id=lead_id,
            event_type=EngagementEvent.OPENED,
            email_number=1,
            metadata={"user_agent": "Chrome"},
        )
        
        assert lead_id in orchestrator._engagement_tracker
        assert len(orchestrator._engagement_tracker[lead_id]) == 1
        
        record = orchestrator._engagement_tracker[lead_id][0]
        assert record.event_type == EngagementEvent.OPENED
        assert record.metadata["user_agent"] == "Chrome"
    
    def test_get_engagement_metrics(self):
        """Test getting engagement metrics for a lead."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        lead_id = 1
        orchestrator.record_engagement(lead_id, EngagementEvent.OPENED, 1)
        orchestrator.record_engagement(lead_id, EngagementEvent.OPENED, 2)
        orchestrator.record_engagement(lead_id, EngagementEvent.CLICKED, 2)
        orchestrator.record_engagement(lead_id, EngagementEvent.REPLIED, 3)
        
        metrics = orchestrator.get_engagement_metrics(lead_id)
        
        assert metrics.total_sent == 4
        assert metrics.opened_count == 2
        assert metrics.clicked_count == 1
        assert metrics.replied_count == 1


class TestNurtureMetrics:
    """Test batch nurture metrics."""
    
    def test_empty_metrics(self):
        """Test empty nurture metrics."""
        metrics = NurtureMetrics()
        
        assert metrics.total_leads == 0
        assert metrics.success_rate == 0.0
        assert metrics.overall_open_rate == 0.0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = NurtureMetrics(
            total_leads=100,
            errors=10,
        )
        
        assert metrics.success_rate == 90.0
    
    def test_avg_emails_per_lead(self):
        """Test average emails per lead."""
        metrics = NurtureMetrics(
            total_leads=50,
            emails_sent=150,
        )
        
        assert metrics.avg_emails_per_lead == 3.0
    
    def test_overall_open_rate(self):
        """Test overall open rate."""
        metrics = NurtureMetrics(
            emails_sent=100,
            opens=45,
        )
        
        assert metrics.overall_open_rate == 45.0
    
    def test_overall_click_rate(self):
        """Test overall click rate."""
        metrics = NurtureMetrics(
            opens=100,
            clicks=25,
        )
        
        assert metrics.overall_click_rate == 25.0
    
    def test_overall_reply_rate(self):
        """Test overall reply rate."""
        metrics = NurtureMetrics(
            emails_sent=200,
            replies=30,
        )
        
        assert metrics.overall_reply_rate == 15.0


class TestEmailTemplates:
    """Test predefined email templates."""
    
    def test_aggressive_close_has_three_emails(self):
        """Test aggressive close has 3 emails."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        for i in range(1, 4):
            template = orchestrator._get_email_template(
                ContentSequenceType.AGGRESSIVE_CLOSE,
                i,
            )
            assert template is not None
            assert template.email_number == i
        
        template = orchestrator._get_email_template(
            ContentSequenceType.AGGRESSIVE_CLOSE,
            4,
        )
        assert template is None
    
    def test_regular_nurture_has_four_emails(self):
        """Test regular nurture has 4 emails."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        for i in range(1, 5):
            template = orchestrator._get_email_template(
                ContentSequenceType.REGULAR_NURTURE,
                i,
            )
            assert template is not None
        
        template = orchestrator._get_email_template(
            ContentSequenceType.REGULAR_NURTURE,
            5,
        )
        assert template is None
    
    def test_long_term_nurture_has_six_emails(self):
        """Test long term nurture has 6 emails."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        for i in range(1, 7):
            template = orchestrator._get_email_template(
                ContentSequenceType.LONG_TERM_NURTURE,
                i,
            )
            assert template is not None
        
        template = orchestrator._get_email_template(
            ContentSequenceType.LONG_TERM_NURTURE,
            7,
        )
        assert template is None
    
    def test_cold_outreach_has_eight_emails(self):
        """Test cold outreach has 8 emails."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        for i in range(1, 9):
            template = orchestrator._get_email_template(
                ContentSequenceType.COLD_OUTREACH,
                i,
            )
            assert template is not None
        
        template = orchestrator._get_email_template(
            ContentSequenceType.COLD_OUTREACH,
            9,
        )
        assert template is None


class TestNurtureWorkflow:
    """Test complete nurture workflows."""
    
    def test_single_lead_nurture_flow(self):
        """Test nurturing a single lead through sequence."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        lead = Lead(
            name="John Smith",
            first_name="John",
            company="Acme",
            title="Sales Director",
            email="john@acme.com",
            source=LeadSource.OTHER,
            status=LeadStatus.ROUTED,
            routing_sequence="aggressive_close",
            sequence_start_at=datetime.utcnow() - timedelta(days=3),
        )
        
        decision = orchestrator.evaluate_lead_nurture(lead)
        assert decision.should_send is True
        assert decision.next_email_number == 1
        
        result = orchestrator.send_email(lead, decision.template, 1)
        assert result.success is True
        
        # send_email already records engagement, so we just check metrics
        lead_id = lead.id
        metrics = orchestrator.get_engagement_metrics(lead_id)
        assert metrics.total_sent == 1
        assert metrics.open_rate == 100.0
    
    def test_multiple_leads_nurture_batch(self):
        """Test nurturing multiple leads in batch."""
        session = MagicMock()
        orchestrator = NurtureOrchestrator(session)
        
        batch_metrics = NurtureMetrics()
        
        # Create 3 leads with sufficient time elapsed
        for i in range(1, 4):
            lead = Lead(
                name=f"Lead {i}",
                first_name=f"Lead{i}",
                email=f"lead{i}@example.com",
                source=LeadSource.OTHER,
                status=LeadStatus.ROUTED,
                routing_sequence="aggressive_close",
                sequence_start_at=datetime.utcnow() - timedelta(days=10),  # 10 days ago
            )
            
            decision = orchestrator.evaluate_lead_nurture(lead)
            if decision.should_send:
                result = orchestrator.send_email(lead, decision.template, 1)
                if result.success:
                    batch_metrics.emails_sent += 1
                    batch_metrics.total_leads += 1
        
        assert batch_metrics.total_leads >= 1
        assert batch_metrics.emails_sent >= 1
    
    def test_engagement_status_update(self):
        """Test status update based on engagement."""
        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = MagicMock(
            id=1,
            status=LeadStatus.ROUTED.value,
        )
        
        orchestrator = NurtureOrchestrator(session)
        
        orchestrator.record_engagement(1, EngagementEvent.REPLIED, 2)
        
        orchestrator.update_lead_status(1, session)
        
        session.commit.assert_called()
