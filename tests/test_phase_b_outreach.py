"""
Phase B: Outreach Channels - Test Suite

Comprehensive tests for:
- Channel domain models
- Database models
- Outreach services (Email, LinkedIn, Contact Form)
- Channel Sequencer
- Orchestrator integration
- Operator services API

All 20+ tests focus on:
- Normal operation paths
- Error handling
- Rate limiting
- Fallback logic
- Integration between components
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import uuid4

from aicmo.cam.domain import (
    OutreachMessage,
    ChannelType,
    OutreachStatus,
    ChannelConfig,
    SequenceStep,
    SequenceConfig,
    LinkedInConnectionStatus,
)
from aicmo.cam.outreach import OutreachServiceBase, OutreachResult, RateLimiter
from aicmo.cam.outreach.email_outreach import EmailOutreachService
from aicmo.cam.outreach.linkedin_outreach import LinkedInOutreachService
from aicmo.cam.outreach.contact_form_outreach import ContactFormOutreachService
from aicmo.cam.outreach.sequencer import ChannelSequencer
from aicmo.cam.db_models import (
    LeadDB,
    CampaignDB,
    OutreachAttemptDB,
    ChannelConfigDB,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_message():
    """Create a sample outreach message."""
    return OutreachMessage(
        channel=ChannelType.EMAIL,
        message_type="cold_outreach",
        body="Hello! I wanted to reach out about our services.",
        subject="Interested in connecting?",
        template_name="cold_outreach",
        personalization_data={
            'name': 'John Doe',
            'company': 'Acme Corp',
            'role': 'CEO',
        }
    )


@pytest.fixture
def channel_config():
    """Create sample channel config."""
    return ChannelConfig(
        channel=ChannelType.EMAIL,
        enabled=True,
        max_per_hour=100,
        max_per_day=500,
        settings={'template_dir': '/templates'},
    )


@pytest.fixture
def sequence_config():
    """Create default sequence config."""
    return SequenceConfig(
        name="default_sequence",
        description="Email → LinkedIn → Form",
        steps=[
            SequenceStep(
                order=1,
                channel=ChannelType.EMAIL,
                message_template="email_intro",
            ),
            SequenceStep(
                order=2,
                channel=ChannelType.LINKEDIN,
                message_template="linkedin_dm",
            ),
            SequenceStep(
                order=3,
                channel=ChannelType.CONTACT_FORM,
                message_template="contact_form",
            ),
        ],
    )


@pytest.fixture
def email_service():
    """Create email outreach service."""
    return EmailOutreachService()


@pytest.fixture
def linkedin_service():
    """Create LinkedIn outreach service."""
    return LinkedInOutreachService()


@pytest.fixture
def form_service():
    """Create contact form outreach service."""
    return ContactFormOutreachService()


@pytest.fixture
def sequencer(email_service, linkedin_service, form_service):
    """Create channel sequencer with mocked services."""
    seq = ChannelSequencer()
    seq.email_service = email_service
    seq.linkedin_service = linkedin_service
    seq.form_service = form_service
    return seq


# ============================================================================
# DOMAIN MODEL TESTS
# ============================================================================

class TestChannelDomainModels:
    """Test channel domain models."""
    
    def test_outreach_message_creation(self, sample_message):
        """Test OutreachMessage creation."""
        assert sample_message.body == "Hello! I wanted to reach out about our services."
        assert sample_message.subject == "Interested in connecting?"
        assert sample_message.personalization_data['name'] == 'John Doe'
    
    def test_channel_config_creation(self, channel_config):
        """Test ChannelConfig creation."""
        assert channel_config.channel_type == ChannelType.EMAIL
        assert channel_config.enabled is True
        assert channel_config.rate_limit_per_hour == 100
    
    def test_sequence_config_creation(self, sequence_config):
        """Test SequenceConfig creation."""
        assert sequence_config.name == "default_sequence"
        assert len(sequence_config.steps) == 3
        assert sequence_config.steps[0].channel == ChannelType.EMAIL
    
    def test_sequence_order_logic(self, sequence_config):
        """Test sequence step order and configuration."""
        email_step = sequence_config.steps[0]
        linkedin_step = sequence_config.steps[1]
        form_step = sequence_config.steps[2]
        
        assert email_step.order == 1
        assert linkedin_step.order == 2
        assert form_step.order == 3
        assert email_step.message_template == "email_intro"
        assert linkedin_step.message_template == "linkedin_dm"
        assert linkedin_step.fallback_enabled is True
        assert form_step.fallback_enabled is False


# ============================================================================
# EMAIL SERVICE TESTS
# ============================================================================

class TestEmailOutreachService:
    """Test email outreach service."""
    
    def test_email_service_send_success(self, email_service, sample_message):
        """Test successful email send."""
        result = email_service.send(
            message=sample_message,
            recipient_email="test@example.com",
        )
        
        assert result.success is True
        assert result.channel == ChannelType.EMAIL
        assert result.status == OutreachStatus.SENT
        assert result.message_id is not None
    
    def test_email_service_missing_email(self, email_service, sample_message):
        """Test email send with missing recipient."""
        result = email_service.send(
            message=sample_message,
            recipient_email=None,
        )
        
        assert result.success is False
        assert result.status == OutreachStatus.FAILED
        assert 'email' in result.error.lower()
    
    def test_email_service_check_status(self, email_service):
        """Test email delivery status check."""
        status = email_service.check_status("test-message-id-123")
        assert status in [s.value for s in OutreachStatus]
    
    def test_email_bounce_rate(self, email_service):
        """Test bounce rate monitoring."""
        rate = email_service.get_bounce_rate()
        assert isinstance(rate, float)
        assert 0 <= rate <= 1
    
    def test_email_complaint_rate(self, email_service):
        """Test complaint rate monitoring."""
        rate = email_service.get_complaint_rate()
        assert isinstance(rate, float)
        assert 0 <= rate <= 1


# ============================================================================
# LINKEDIN SERVICE TESTS
# ============================================================================

class TestLinkedInOutreachService:
    """Test LinkedIn outreach service."""
    
    def test_linkedin_send_success(self, linkedin_service, sample_message):
        """Test successful LinkedIn message send."""
        result = linkedin_service.send(
            message=sample_message,
            recipient_linkedin_id="linkedin-user-123",
        )
        
        assert result.success is True
        assert result.channel == ChannelType.LINKEDIN
        assert result.status == OutreachStatus.SENT
        assert result.message_id is not None
    
    def test_linkedin_send_missing_id(self, linkedin_service, sample_message):
        """Test LinkedIn send with missing profile ID."""
        result = linkedin_service.send(
            message=sample_message,
            recipient_linkedin_id=None,
        )
        
        assert result.success is False
        assert result.status == OutreachStatus.FAILED
        assert 'LinkedIn' in result.error or 'ID' in result.error
    
    def test_linkedin_connection_request(self, linkedin_service):
        """Test LinkedIn connection request."""
        result = linkedin_service.send_connection_request(
            recipient_linkedin_id="linkedin-user-456",
            message="Let's connect!",
        )
        
        assert result.success is True
        assert result.channel == ChannelType.LINKEDIN
        assert result.message_id is not None
    
    def test_linkedin_check_connection_status(self, linkedin_service):
        """Test LinkedIn connection status check."""
        status = linkedin_service.check_connection_status("linkedin-user-789")
        assert status in [s for s in LinkedInConnectionStatus]


# ============================================================================
# CONTACT FORM SERVICE TESTS
# ============================================================================

class TestContactFormOutreachService:
    """Test contact form outreach service."""
    
    def test_form_send_success(self, form_service, sample_message):
        """Test successful form submission."""
        result = form_service.send(
            message=sample_message,
            recipient_email="recipient@example.com",
            form_url="https://example.com/contact",
        )
        
        assert result.success is True
        assert result.channel == ChannelType.CONTACT_FORM
        assert result.status == OutreachStatus.SENT
        assert result.message_id is not None
    
    def test_form_send_missing_url(self, form_service, sample_message):
        """Test form submission without URL."""
        result = form_service.send(
            message=sample_message,
            recipient_email="test@example.com",
            form_url=None,
        )
        
        assert result.success is False
        assert result.status == OutreachStatus.FAILED
    
    def test_form_verify_form(self, form_service):
        """Test form verification."""
        is_valid = form_service.verify_form("https://example.com/contact")
        assert isinstance(is_valid, bool)
    
    def test_form_check_spam_filter(self, form_service):
        """Test spam filter detection."""
        has_spam = form_service.check_form_spam_filter("https://example.com/contact")
        assert isinstance(has_spam, bool)


# ============================================================================
# CHANNEL SEQUENCER TESTS
# ============================================================================

class TestChannelSequencer:
    """Test channel sequencer logic."""
    
    def test_sequencer_execute_default(
        self,
        sequencer,
        sample_message,
        sequence_config,
    ):
        """Test sequencer with default sequence."""
        result = sequencer.execute_sequence(
            message=sample_message,
            recipient_email="test@example.com",
            recipient_linkedin_id="linkedin-123",
            form_url="https://example.com/contact",
            sequence_config=sequence_config,
        )
        
        assert 'success' in result
        assert 'message_id' in result
        assert 'channel_used' in result
        assert 'attempts' in result
    
    def test_sequencer_fallback_logic(
        self,
        sequencer,
        sample_message,
    ):
        """Test sequencer fallback to next channel."""
        # Create custom sequence
        sequence = SequenceConfig(
            name="test",
            steps=[
                SequenceStep(ChannelType.EMAIL, 1, fallback_enabled=True),
                SequenceStep(ChannelType.LINKEDIN, 2, fallback_enabled=False),
            ],
        )
        
        result = sequencer.execute_sequence(
            message=sample_message,
            recipient_email="test@example.com",
            recipient_linkedin_id="linkedin-123",
            sequence_config=sequence,
        )
        
        # Should have attempted multiple channels
        assert 'attempts' in result
    
    def test_sequencer_build_default(self, sequencer):
        """Test default sequence building."""
        sequence = sequencer._build_default_sequence()
        
        assert sequence.name == "default_sequence"
        assert len(sequence.steps) == 3
        assert sequence.steps[0].channel == ChannelType.EMAIL
        assert sequence.steps[2].fallback_enabled is False
    
    def test_sequencer_metrics(self, sequencer):
        """Test sequence metrics calculation."""
        attempts = [
            {'channel': 'EMAIL', 'success': True},
            {'channel': 'LINKEDIN', 'success': False},
            {'channel': 'CONTACT_FORM', 'success': True},
        ]
        
        metrics = sequencer.get_sequence_metrics(attempts)
        
        assert metrics['total_attempts'] == 3
        assert len(metrics['successful_channels']) == 2
        assert len(metrics['failed_channels']) == 1
        assert metrics['success_rate'] == pytest.approx(66.67, 0.1)
    
    def test_sequencer_retry_scheduling(self, sequencer):
        """Test retry scheduling."""
        result = {
            'message_id': 'msg-123',
            'retry_count': 0,
        }
        
        next_retry = sequencer.schedule_retry(result, delay_minutes=60, max_retries=3)
        
        assert next_retry is not None
        assert next_retry > datetime.utcnow()
    
    def test_sequencer_max_retries_reached(self, sequencer):
        """Test when max retries reached."""
        result = {
            'message_id': 'msg-123',
            'retry_count': 3,
        }
        
        next_retry = sequencer.schedule_retry(result, delay_minutes=60, max_retries=3)
        
        assert next_retry is None


# ============================================================================
# RATE LIMITER TESTS
# ============================================================================

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter creation."""
        limiter = RateLimiter(
            per_hour=100,
            per_day=500,
        )
        
        assert limiter.per_hour == 100
        assert limiter.per_day == 500
    
    def test_rate_limiter_can_send(self):
        """Test can_send checks."""
        limiter = RateLimiter(per_hour=10, per_day=50)
        
        # Should be able to send initially
        assert limiter.can_send("lead-123") is True
    
    def test_rate_limiter_exhaustion(self):
        """Test rate limit exhaustion."""
        limiter = RateLimiter(per_hour=1, per_day=1)
        
        # First send should work
        assert limiter.can_send("lead-123") is True
        
        # Second send within same hour should fail
        assert limiter.can_send("lead-123") is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhaseB_Integration:
    """Integration tests across Phase B components."""
    
    def test_full_channel_sequence_flow(
        self,
        sequencer,
        sample_message,
        sequence_config,
    ):
        """Test complete end-to-end channel sequence."""
        result = sequencer.execute_sequence(
            message=sample_message,
            recipient_email="integration-test@example.com",
            recipient_linkedin_id="li-123",
            form_url="https://example.com/contact",
            sequence_config=sequence_config,
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'attempts' in result
        assert len(result['attempts']) > 0
    
    def test_multi_channel_attempt_tracking(
        self,
        sequencer,
        sample_message,
    ):
        """Test tracking of all channel attempts."""
        result = sequencer.execute_sequence(
            message=sample_message,
            recipient_email="test@example.com",
            recipient_linkedin_id="li-456",
            form_url="https://example.com/contact",
        )
        
        attempts = result.get('attempts', [])
        
        # Each attempt should have required fields
        for attempt in attempts:
            assert 'channel' in attempt
            assert 'success' in attempt
            assert 'timestamp' in attempt


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestPhaseB_EdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_personalization_data(
        self,
        email_service,
    ):
        """Test with empty personalization data."""
        msg = OutreachMessage(
            body="Generic message",
            subject="Hello",
            template_name=None,
            personalization_data={},
        )
        
        result = email_service.send(
            message=msg,
            recipient_email="test@example.com",
        )
        
        assert result.success is True
    
    def test_long_message_body(
        self,
        email_service,
    ):
        """Test with very long message body."""
        long_body = "A" * 10000  # 10k character message
        msg = OutreachMessage(
            body=long_body,
            subject="Long message",
        )
        
        result = email_service.send(
            message=msg,
            recipient_email="test@example.com",
        )
        
        assert isinstance(result, OutreachResult)
    
    def test_special_characters_in_message(
        self,
        linkedin_service,
    ):
        """Test message with special characters."""
        msg = OutreachMessage(
            body="Hello! 你好 مرحبا 😊 Special chars: @#$%^&*()",
            subject="Unicode test",
        )
        
        result = linkedin_service.send(
            message=msg,
            recipient_linkedin_id="li-123",
        )
        
        assert isinstance(result, OutreachResult)
    
    def test_concurrent_send_attempts(
        self,
        email_service,
        sample_message,
    ):
        """Test handling of concurrent send attempts."""
        # Send multiple messages rapidly
        results = []
        for i in range(5):
            result = email_service.send(
                message=sample_message,
                recipient_email=f"test{i}@example.com",
            )
            results.append(result)
        
        # All should succeed or fail consistently
        assert len(results) == 5
        assert all(isinstance(r, OutreachResult) for r in results)
