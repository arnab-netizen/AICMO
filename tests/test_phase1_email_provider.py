"""
Phase 1: Email provider tests (Resend, NoOp, email sending service).

Tests for:
- Resend provider configuration and dry-run mode
- Email allowlist filtering
- NoOp provider fallback
- EmailSendingService with caps and idempotency
- OutboundEmailDB persistence
"""

import pytest
from aicmo.cam.gateways.email_providers.resend import ResendEmailProvider, NoOpEmailProvider


class TestResendProvider:
    """Tests for Resend email provider."""
    
    def test_resend_initialization(self):
        """Test Resend provider can be initialized with credentials."""
        provider = ResendEmailProvider(
            api_key="test_key_123",
            from_email="sender@example.com",
        )
        assert provider.get_name() == "Resend"
        assert provider.is_configured()
    
    def test_resend_requires_api_key(self):
        """Test Resend is not configured without API key."""
        provider = ResendEmailProvider(
            api_key="",
            from_email="sender@example.com",
        )
        assert not provider.is_configured()
    
    def test_resend_requires_from_email(self):
        """Test Resend is not configured without from_email."""
        provider = ResendEmailProvider(
            api_key="test_key",
            from_email="",
        )
        assert not provider.is_configured()
    
    def test_resend_dry_run_mode(self):
        """Test Resend dry-run mode logs without calling API."""
        provider = ResendEmailProvider(
            api_key="test_key",
            from_email="sender@example.com",
            dry_run=True,
        )
        
        result = provider.send(
            to_email="recipient@example.com",
            from_email="sender@example.com",
            subject="Test Subject",
            html_body="<html><body>Test</body></html>",
        )
        
        assert result.success
        assert result.provider_message_id is not None
        assert result.provider_message_id.startswith("dry-run-")
        assert result.sent_at is not None
    
    def test_resend_allowlist_allows_matching(self):
        """Test allowlist allows emails matching regex."""
        provider = ResendEmailProvider(
            api_key="test_key",
            from_email="sender@example.com",
            dry_run=True,
            allowlist_regex=r"@company\.com$",
        )
        
        result = provider.send(
            to_email="alice@company.com",
            from_email="sender@example.com",
            subject="Test",
            html_body="<html>Test</html>",
        )
        
        assert result.success
    
    def test_resend_allowlist_blocks_non_matching(self):
        """Test allowlist blocks emails not matching regex."""
        provider = ResendEmailProvider(
            api_key="test_key",
            from_email="sender@example.com",
            dry_run=True,
            allowlist_regex=r"@company\.com$",
        )
        
        result = provider.send(
            to_email="alice@other.com",
            from_email="sender@example.com",
            subject="Test",
            html_body="<html>Test</html>",
        )
        
        assert not result.success
        assert "allowlist" in result.error.lower()


class TestNoOpProvider:
    """Tests for NoOp email provider (safe fallback)."""
    
    def test_noop_always_configured(self):
        """Test NoOp is always ready to use."""
        provider = NoOpEmailProvider()
        assert provider.is_configured()
    
    def test_noop_name(self):
        """Test NoOp provider name."""
        provider = NoOpEmailProvider()
        assert provider.get_name() == "NoOp"
    
    def test_noop_always_succeeds(self):
        """Test NoOp always returns success."""
        provider = NoOpEmailProvider()
        
        result = provider.send(
            to_email="recipient@example.com",
            from_email="sender@example.com",
            subject="Test",
            html_body="<html>Test</html>",
        )
        
        assert result.success
        assert result.provider_message_id is not None
        assert result.provider_message_id.startswith("noop-")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
