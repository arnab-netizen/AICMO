"""
End-to-End Smoke Test for Modular CAM Architecture

Tests one complete worker cycle with:
- Mock database tables
- Fake/no-op email provider (no real sends)
- Fake inbox provider (no real IMAP connects)
- All 7 steps executable
- Validates cycle completion and result structure
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from aicmo.cam.db_models import Base, CampaignDB, LeadDB, OutboundEmailDB, InboundEmailDB
from aicmo.platform.orchestration import DIContainer, ModuleRegistry
from aicmo.cam.composition import CamFlowRunner, CycleResult
from aicmo.cam.contracts import (
    SendEmailRequest,
    SendEmailResponse,
    ClassifyReplyRequest,
    ClassifyReplyResponse,
    ReplyClassificationEnum,
    EmailReplyModel,
    FetchInboxResponse,
)


# ─────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    
    yield session
    
    session.close()


@pytest.fixture
def test_campaign(db_session):
    """Create a test campaign."""
    campaign = CampaignDB(
        name="Test Campaign",
        description="E2E smoke test campaign",
        status="RUNNING",
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest.fixture
def test_leads(db_session, test_campaign):
    """Create test leads."""
    leads = []
    for i in range(3):
        lead = LeadDB(
            campaign_id=test_campaign.id,
            first_name=f"Lead{i}",
            last_name=f"Test",
            email=f"lead{i}@example.com",
            status="PROSPECT",
        )
        db_session.add(lead)
        leads.append(lead)
    
    db_session.commit()
    return leads


@pytest.fixture
def test_queued_emails(db_session, test_campaign, test_leads):
    """Create queued outbound emails."""
    emails = []
    for i, lead in enumerate(test_leads[:2]):  # Queue emails for first 2 leads
        email = OutboundEmailDB(
            campaign_id=test_campaign.id,
            lead_id=lead.id,
            to_email=lead.email,
            from_email="noreply@example.com",
            subject=f"Test Email {i}",
            html_body=f"<p>Test content {i}</p>",
            provider="NoOp",
            sequence_number=1,
            status="QUEUED",
        )
        db_session.add(email)
        emails.append(email)
    
    db_session.commit()
    return emails


@pytest.fixture
def test_inbound_emails(db_session, test_campaign, test_leads):
    """Create inbound (reply) emails."""
    replies = []
    for i, lead in enumerate(test_leads[:2]):  # Create replies for first 2 leads
        reply = InboundEmailDB(
            campaign_id=test_campaign.id,
            lead_id=lead.id,
            from_email=lead.email,
            to_email="noreply@example.com",
            subject="Re: Test Email",
            body_text="I'm very interested!",
            provider="IMAP",
            provider_msg_uid=f"imap_uid_{i}",
            received_at=datetime.utcnow(),
        )
        db_session.add(reply)
        replies.append(reply)
    
    db_session.commit()
    return replies


# ─────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────

class TestE2EModularCycle:
    """End-to-end tests for the complete modular worker cycle."""
    
    def test_di_container_initialization(self, db_session):
        """Test: DIContainer initializes with all modules."""
        container, registry = DIContainer.create_default(db_session)
        
        # Verify all 6 modules present
        services = container.get_all_services()
        assert len(services) == 6
        assert "EmailModule" in services
        assert "ClassificationModule" in services
        assert "FollowUpModule" in services
        assert "DecisionModule" in services
        assert "InboxModule" in services
        assert "AlertModule" in services
        
        # Verify registry tracks modules
        modules = registry.get_all()
        assert len(modules) == 6
    
    def test_flow_runner_initialization(self, db_session):
        """Test: CamFlowRunner initializes successfully."""
        container, registry = DIContainer.create_default(db_session)
        runner = CamFlowRunner(container, registry, db_session)
        
        assert runner.container == container
        assert runner.registry == registry
        assert runner.db_session == db_session
        assert runner.cycle_number == 0
    
    def test_cycle_step_send_emails(self, db_session, test_queued_emails):
        """Test: Step 1 (Send Emails) executes successfully."""
        container, registry = DIContainer.create_default(db_session)
        runner = CamFlowRunner(container, registry, db_session)
        
        # Execute step
        result = runner._step_send_emails()
        
        # Verify result
        assert result.step_number == 1
        assert result.step_name == "SendEmails"
        assert result.success is True
        assert result.items_processed == len(test_queued_emails)
        
        # Verify emails marked as sent
        sent_emails = db_session.query(OutboundEmailDB).filter_by(status="SENT").all()
        assert len(sent_emails) == len(test_queued_emails)
    
    def test_cycle_step_classify_replies(self, db_session, test_inbound_emails):
        """Test: Step 3 (Classify Replies) executes successfully."""
        container, registry = DIContainer.create_default(db_session)
        runner = CamFlowRunner(container, registry, db_session)
        
        # Verify emails are unclassified
        unclassified = db_session.query(InboundEmailDB).filter(
            InboundEmailDB.classification.is_(None)
        ).all()
        assert len(unclassified) == len(test_inbound_emails)
        
        # Execute step
        result = runner._step_classify_and_process_replies()
        
        # Verify result
        assert result.step_number == 3
        assert result.success is True
        assert result.items_processed == len(test_inbound_emails)
        
        # Verify emails classified
        classified = db_session.query(InboundEmailDB).filter(
            InboundEmailDB.classification.isnot(None)
        ).all()
        assert len(classified) == len(test_inbound_emails)
        
        # Verify classification is valid
        for email in classified:
            assert email.classification in [
                "POSITIVE", "NEGATIVE", "OOO", "BOUNCE", "UNSUB", "NEUTRAL"
            ]
    
    def test_cycle_all_steps_sequence(self, db_session, test_campaign, test_queued_emails, test_inbound_emails):
        """Test: All 7 steps execute in sequence successfully."""
        container, registry = DIContainer.create_default(db_session)
        runner = CamFlowRunner(container, registry, db_session)
        
        # Execute one complete cycle
        result = runner.run_one_cycle()
        
        # Verify cycle result structure
        assert isinstance(result, CycleResult)
        assert result.cycle_number == 1
        assert result.success is True
        assert result.duration_seconds > 0
        assert len(result.steps) == 7
        
        # Verify each step has result
        step_names = [s.step_name for s in result.steps]
        expected_steps = [
            "SendEmails",
            "PollInbox",
            "ClassifyAndProcess",
            "NoReplyTimeouts",
            "ComputeMetrics",
            "EvaluateCampaigns",
            "DispatchAlerts",
        ]
        assert step_names == expected_steps
        
        # Verify at least some steps succeeded
        successful_steps = sum(1 for s in result.steps if s.success)
        assert successful_steps >= 1
    
    def test_cycle_result_serialization(self, db_session, test_campaign, test_queued_emails):
        """Test: CycleResult can be serialized to dict."""
        container, registry = DIContainer.create_default(db_session)
        runner = CamFlowRunner(container, registry, db_session)
        
        result = runner.run_one_cycle()
        result_dict = result.to_dict()
        
        # Verify dict structure
        assert "cycle_number" in result_dict
        assert "timestamp" in result_dict
        assert "success" in result_dict
        assert "duration_seconds" in result_dict
        assert "steps" in result_dict
        
        # Verify steps are serialized
        assert len(result_dict["steps"]) == 7
        assert result_dict["steps"][0]["step_name"] == "SendEmails"
    
    def test_cycle_idempotency(self, db_session, test_campaign, test_queued_emails, test_inbound_emails):
        """Test: Running cycle twice doesn't create duplicates (idempotent)."""
        container, registry = DIContainer.create_default(db_session)
        runner = CamFlowRunner(container, registry, db_session)
        
        # Run cycle twice
        result1 = runner.run_one_cycle()
        result2 = runner.run_one_cycle()
        
        # Both cycles should succeed
        assert result1.success
        assert result2.success
        
        # Second cycle should be cycle 2
        assert result1.cycle_number == 1
        assert result2.cycle_number == 2
        
        # Verify no duplicate emails were created
        sent_count = db_session.query(OutboundEmailDB).filter_by(status="SENT").count()
        assert sent_count == len(test_queued_emails)  # Should not double
    
    def test_registry_health_tracking(self, db_session):
        """Test: ModuleRegistry tracks module health."""
        container, registry = DIContainer.create_default(db_session)
        
        # Verify initial health
        all_modules = registry.get_all()
        for module in all_modules.values():
            assert module.health_status in ["HEALTHY", "UNHEALTHY", "UNKNOWN", "DEGRADED"]
        
        # Test can_start_worker
        can_start, reason = registry.can_start_worker()
        assert isinstance(can_start, bool)
        assert isinstance(reason, str)
    
    def test_contracts_passed_through_ports(self, db_session, test_queued_emails):
        """
        Test: Module communication uses contract models exclusively.
        
        Verifies that:
        - EmailModule receives SendEmailRequest contract
        - EmailModule returns SendEmailResponse contract
        - All communication is type-safe
        """
        container, registry = DIContainer.create_default(db_session)
        
        # Get EmailModule
        email_module = container.get_service("EmailModule")
        assert email_module is not None
        
        # Create request contract
        request = SendEmailRequest(
            campaign_id=1,
            lead_id=1,
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
            sequence_number=1,
        )
        
        # Send through port (should accept and return contract)
        response = email_module.send_email(request)
        
        # Verify response is contract
        assert isinstance(response, SendEmailResponse)
        assert hasattr(response, 'success')
        assert hasattr(response, 'outbound_email_id')
        assert hasattr(response, 'provider_message_id')
        assert hasattr(response, 'error')


class TestModuleIsolation:
    """Test that modules work independently (solo mode)."""
    
    def test_classifier_works_standalone(self, db_session):
        """Test: ReplyClassifier works without other modules."""
        container, registry = DIContainer.create_default(db_session)
        classifier = container.get_service("ClassificationModule")
        
        # Classify various text examples
        test_cases = [
            ("I'm very interested in this", ReplyClassificationEnum.POSITIVE),
            ("Not interested", ReplyClassificationEnum.NEGATIVE),
            ("Out of office until next week", ReplyClassificationEnum.OOO),
            ("Delivery failed", ReplyClassificationEnum.BOUNCE),
            ("Unsubscribe me", ReplyClassificationEnum.UNSUB),
        ]
        
        for body, expected_classification in test_cases:
            request = ClassifyReplyRequest(subject="", body=body)
            response = classifier.classify(request)
            
            assert response.classification is not None
            assert response.confidence >= 0.0
            assert response.confidence <= 1.0
    
    def test_decision_engine_works_standalone(self, db_session, test_campaign):
        """Test: DecisionEngine works without other modules."""
        container, registry = DIContainer.create_default(db_session)
        decision_module = container.get_service("DecisionModule")
        
        # Compute metrics should not raise
        metrics = decision_module.compute_metrics(test_campaign.id)
        
        assert metrics is not None
        assert hasattr(metrics, 'sent_count')
        assert hasattr(metrics, 'reply_count')


# ─────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
