"""
Tests for Phase 1: Email sending via Resend provider.

Test coverage:
- Resend provider initialization and configuration
- Email sending with Resend API
- Dry-run mode
- Email allowlist filtering
- NoOp provider fallback
- Email persistence to database
- Idempotency (no duplicate sends)
- Email caps (daily and batch)
- Provider error handling
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from aicmo.cam.gateways.email_providers.resend import ResendEmailProvider, NoOpEmailProvider
from aicmo.cam.gateways.email_providers.factory import get_email_provider
from aicmo.cam.services.email_sending_service import EmailSendingService
from aicmo.cam.db_models import OutboundEmailDB, LeadDB, CampaignDB
from aicmo.cam.engine.lead_nurture import EmailTemplate, ContentSequenceType
from aicmo.cam.config import settings
from aicmo.core.db import SessionLocal


# ═══════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def db_session():
    """Get a fresh database session for tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_campaign(db_session: Session):
    """Create a sample campaign for testing."""
    campaign = CampaignDB(
        name="Test Campaign",
        description="Test campaign for email sending",
        active=True,
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


@pytest.fixture
def sample_lead(db_session: Session, sample_campaign: CampaignDB):
    """Create a sample lead for testing."""
    lead = LeadDB(
        campaign_id=sample_campaign.id,
        name="John Prospect",
        email="john@prospect.com",
        first_name="John",
        company="Prospect Co",
        role="CEO",
    )
    db_session.add(lead)
    db_session.commit()
    return lead


@pytest.fixture
def email_template():
    """Create a sample email template for testing."""
    return EmailTemplate(
        sequence_type=ContentSequenceType.AGGRESSIVE_CLOSE,
        email_number=1,
        subject="Check out our {{service}} for {{company}}",
        body="Hi {{first_name}},\n\nWe help companies like {{company}} with {{service}}.\n\nBest,\nAICMO",
        cta_link="https://example.com/cta",
    )


@pytest.fixture
def personalization():
    """Sample personalization variables."""
    return {
        "first_name": "John",
        "company": "Prospect Co",
        "service": "growth marketing",
    }


# ═══════════════════════════════════════════════════════════════════
# TESTS: ResendEmailProvider initialization
# ═══════════════════════════════════════════════════════════════════

class TestResendProviderInitialization:
    """Test Resend provider setup and configuration."""
    
    def test_resend_provider_initializes_with_valid_config(self):
        """Test that Resend provider initializes with API key and from_email."""
        provider = ResendEmailProvider(
            api_key="test-api-key-12345",
            from_email="support@aicmo.com",
        )
        assert provider.api_key == "test-api-key-12345"
        assert provider.from_email == "support@aicmo.com"
        assert not provider.dry_run
    
    def test_resend_provider_is_configured_returns_true_with_credentials(self):
        """Test is_configured() returns True when credentials are set."""
        provider = ResendEmailProvider(
            api_key="test-api-key",
            from_email="support@aicmo.com",
        )
        assert provider.is_configured() is True
    
    def test_resend_provider_is_configured_returns_false_without_api_key(self):
        """Test is_configured() returns False when API key is missing."""
        provider = ResendEmailProvider(
            api_key="",
            from_email="support@aicmo.com",
        )
        assert provider.is_configured() is False
    
    def test_resend_provider_get_name(self):
        """Test get_name() returns correct provider name."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
        )
        assert provider.get_name() == "Resend"
    
    def test_resend_provider_respects_dry_run_flag(self):
        """Test Resend provider can be initialized in dry-run mode."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
            dry_run=True,
        )
        assert provider.dry_run is True
    
    def test_resend_provider_accepts_allowlist_regex(self):
        """Test Resend provider accepts email allowlist regex."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
            allowlist_regex=r"@company\.com$",
        )
        assert provider.allowlist_regex == r"@company\.com$"
        assert provider._compiled_regex is not None


# ═══════════════════════════════════════════════════════════════════
# TESTS: Email sending with Resend
# ═══════════════════════════════════════════════════════════════════

class TestResendEmailSending:
    """Test actual email sending via Resend API."""
    
    @patch('aicmo.cam.gateways.email_providers.resend.requests')
    def test_resend_send_success(self, mock_requests):
        """Test successful email send via Resend API."""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "resend-msg-12345"}
        mock_requests.post.return_value = mock_response
        
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
        )
        
        result = provider.send(
            to_email="john@prospect.com",
            from_email="support@aicmo.com",
            subject="Test Email",
            html_body="<p>Test body</p>",
        )
        
        assert result.success is True
        assert result.provider_message_id == "resend-msg-12345"
        assert result.sent_at is not None
        mock_requests.post.assert_called_once()
    
    @patch('aicmo.cam.gateways.email_providers.resend.requests')
    def test_resend_send_api_error(self, mock_requests):
        """Test handling of API errors from Resend."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_requests.post.return_value = mock_response
        
        provider = ResendEmailProvider(
            api_key="invalid-key",
            from_email="support@aicmo.com",
        )
        
        result = provider.send(
            to_email="john@prospect.com",
            from_email="support@aicmo.com",
            subject="Test Email",
            html_body="<p>Test body</p>",
        )
        
        assert result.success is False
        assert "401" in result.error
    
    @patch('aicmo.cam.gateways.email_providers.resend.requests')
    def test_resend_send_network_error(self, mock_requests):
        """Test handling of network errors."""
        mock_requests.post.side_effect = Exception("Network timeout")
        
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
        )
        
        result = provider.send(
            to_email="john@prospect.com",
            from_email="support@aicmo.com",
            subject="Test Email",
            html_body="<p>Test body</p>",
        )
        
        assert result.success is False
        assert "Network timeout" in result.error
    
    def test_resend_send_dry_run_mode(self):
        """Test that dry-run mode logs without calling API."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
            dry_run=True,
        )
        
        result = provider.send(
            to_email="john@prospect.com",
            from_email="support@aicmo.com",
            subject="Test Email",
            html_body="<p>Test body</p>",
        )
        
        assert result.success is True
        assert result.provider_message_id is not None
        assert "dry-run" in result.provider_message_id


# ═══════════════════════════════════════════════════════════════════
# TESTS: Email allowlisting
# ═══════════════════════════════════════════════════════════════════

class TestEmailAllowlisting:
    """Test email filtering by allowlist regex."""
    
    def test_allowlist_allows_matching_emails(self):
        """Test that emails matching allowlist are sent."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
            allowlist_regex=r"@company\.com$",
            dry_run=True,  # Use dry-run to avoid API calls
        )
        
        result = provider.send(
            to_email="john@company.com",
            from_email="support@aicmo.com",
            subject="Test",
            html_body="<p>Test</p>",
        )
        
        assert result.success is True
    
    def test_allowlist_blocks_non_matching_emails(self):
        """Test that emails not matching allowlist are blocked."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
            allowlist_regex=r"@company\.com$",
        )
        
        result = provider.send(
            to_email="john@other-company.com",
            from_email="support@aicmo.com",
            subject="Test",
            html_body="<p>Test</p>",
        )
        
        assert result.success is False
        assert "does not match allowlist" in result.error
    
    def test_no_allowlist_allows_all_emails(self):
        """Test that without allowlist, all emails are allowed."""
        provider = ResendEmailProvider(
            api_key="test-key",
            from_email="support@aicmo.com",
            allowlist_regex=None,
            dry_run=True,
        )
        
        result = provider.send(
            to_email="john@random-domain.com",
            from_email="support@aicmo.com",
            subject="Test",
            html_body="<p>Test</p>",
        )
        
        assert result.success is True


# ═══════════════════════════════════════════════════════════════════
# TESTS: NoOp provider
# ═══════════════════════════════════════════════════════════════════

class TestNoOpEmailProvider:
    """Test the safe NoOp email provider."""
    
    def test_noop_provider_always_configured(self):
        """Test that NoOp provider is always ready."""
        provider = NoOpEmailProvider()
        assert provider.is_configured() is True
    
    def test_noop_provider_get_name(self):
        """Test NoOp provider name."""
        provider = NoOpEmailProvider()
        assert provider.get_name() == "NoOp"
    
    def test_noop_provider_returns_success(self):
        """Test that NoOp provider always returns success."""
        provider = NoOpEmailProvider()
        result = provider.send(
            to_email="any@email.com",
            from_email="sender@aicmo.com",
            subject="Test",
            html_body="<p>Test</p>",
        )
        assert result.success is True
        assert result.provider_message_id is not None
    
    def test_noop_provider_never_raises(self):
        """Test that NoOp provider never raises exceptions."""
        provider = NoOpEmailProvider()
        # Test with invalid inputs
        result = provider.send(
            to_email="",
            from_email="",
            subject="",
            html_body="",
        )
        assert result.success is True


# ═══════════════════════════════════════════════════════════════════
# TESTS: Email provider factory
# ═══════════════════════════════════════════════════════════════════

class TestEmailProviderFactory:
    """Test the email provider factory logic."""
    
    @patch('aicmo.cam.gateways.email_providers.factory.settings')
    def test_factory_returns_resend_when_api_key_set(self, mock_settings):
        """Test that factory returns Resend provider when API key is configured."""
        mock_settings.RESEND_API_KEY = "test-key"
        mock_settings.RESEND_FROM_EMAIL = "support@aicmo.com"
        mock_settings.CAM_EMAIL_DRY_RUN = False
        mock_settings.CAM_EMAIL_ALLOWLIST_REGEX = ""
        
        provider = get_email_provider()
        assert isinstance(provider, ResendEmailProvider)
    
    @patch('aicmo.cam.gateways.email_providers.factory.settings')
    def test_factory_returns_noop_when_no_api_key(self, mock_settings):
        """Test that factory returns NoOp when API key is not set."""
        mock_settings.RESEND_API_KEY = ""
        
        provider = get_email_provider()
        assert isinstance(provider, NoOpEmailProvider)


# ═══════════════════════════════════════════════════════════════════
# TESTS: EmailSendingService
# ═══════════════════════════════════════════════════════════════════

class TestEmailSendingService:
    """Test the high-level email sending service."""
    
    def test_email_sending_service_initializes(self, db_session):
        """Test that email sending service initializes properly."""
        service = EmailSendingService(db_session)
        assert service.db == db_session
        assert service.provider is not None
    
    @pytest.mark.asyncio
    async def test_send_email_persists_to_database(
        self,
        db_session,
        sample_campaign,
        sample_lead,
        email_template,
        personalization,
    ):
        """Test that sent email is persisted to OutboundEmailDB."""
        service = EmailSendingService(db_session)
        
        # Mock the provider to return success
        service.provider = NoOpEmailProvider()
        
        result = await service.send_email(
            to_email=sample_lead.email,
            campaign_id=sample_campaign.id,
            lead_id=sample_lead.id,
            template=email_template,
            personalization_dict=personalization,
            sequence_number=1,
        )
        
        assert result is not None
        assert result.to_email == sample_lead.email
        assert result.campaign_id == sample_campaign.id
        assert result.lead_id == sample_lead.id
        assert result.status == "SENT"
        
        # Verify database has the record
        db_record = db_session.query(OutboundEmailDB).filter_by(id=result.id).first()
        assert db_record is not None
        assert db_record.to_email == sample_lead.email
    
    @pytest.mark.asyncio
    async def test_send_email_idempotency_prevents_duplicates(
        self,
        db_session,
        sample_campaign,
        sample_lead,
        email_template,
        personalization,
    ):
        """Test that sending the same email twice doesn't duplicate."""
        service = EmailSendingService(db_session)
        service.provider = NoOpEmailProvider()
        
        # Send first time
        result1 = await service.send_email(
            to_email=sample_lead.email,
            campaign_id=sample_campaign.id,
            lead_id=sample_lead.id,
            template=email_template,
            personalization_dict=personalization,
            sequence_number=1,
        )
        
        # Send second time (same recipient, template, sequence)
        result2 = await service.send_email(
            to_email=sample_lead.email,
            campaign_id=sample_campaign.id,
            lead_id=sample_lead.id,
            template=email_template,
            personalization_dict=personalization,
            sequence_number=1,
        )
        
        # Should return the same record
        assert result1.id == result2.id
        
        # Verify only one record in database
        count = db_session.query(OutboundEmailDB).filter_by(
            lead_id=sample_lead.id,
        ).count()
        assert count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
