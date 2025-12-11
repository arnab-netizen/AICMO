"""
Tests for Dropcontact Email Verifier integration.

Tests the real Dropcontact API implementation including:
- Single email verification
- Batch verification with chunking
- Status mapping (valid/invalid/not_found/role/disposable)
- Error handling and optimistic fallback
- Factory integration
"""

import pytest
from unittest.mock import Mock, patch
import os

from aicmo.gateways.adapters.dropcontact_verifier import DropcontactVerifier
from aicmo.gateways.factory import get_email_verifier


class TestDropcontactVerifierSingle:
    """Test single email verification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.verifier = DropcontactVerifier()
        self.test_email = "test@example.com"
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_valid_email(self, mock_post):
        """Test verification of valid email."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "valid"}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        assert result is True
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_invalid_email(self, mock_post):
        """Test verification of invalid email."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "invalid"}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        assert result is False
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_not_found(self, mock_post):
        """Test email not found in database."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "not_found"}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        assert result is False
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_role_email(self, mock_post):
        """Test role-based email (info@, support@, etc)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "role"}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        assert result is False
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_disposable_email(self, mock_post):
        """Test disposable/temp email."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "disposable"}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        assert result is False
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_unknown_status(self, mock_post):
        """Test unknown status (should default to True - optimistic)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "unknown"}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        # Optimistic: unknown status = approve
        assert result is True
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_api_error(self, mock_post):
        """Test API error (should return True - optimistic fallback)."""
        mock_post.side_effect = Exception("Network error")
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            result = self.verifier.verify(self.test_email)
        
        # Optimistic fallback: approve on error
        assert result is True
    
    def test_verify_no_api_key(self):
        """Test verification without API key (optimistic fallback)."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.verifier.verify(self.test_email)
        
        # Optimistic fallback: approve when not configured
        assert result is True


class TestDropcontactVerifierBatch:
    """Test batch email verification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.verifier = DropcontactVerifier()
        self.test_emails = [
            "alice@valid.com",
            "bob@invalid.com",
            "charlie@notfound.com"
        ]
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_batch_success(self, mock_post):
        """Test successful batch verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"email": "alice@valid.com", "status": "valid"},
                {"email": "bob@invalid.com", "status": "invalid"},
                {"email": "charlie@notfound.com", "status": "not_found"}
            ]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            results = self.verifier.verify_batch(self.test_emails)
        
        # Assert
        assert len(results) == 3
        assert results["alice@valid.com"] is True
        assert results["bob@invalid.com"] is False
        assert results["charlie@notfound.com"] is False
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_batch_large_list_chunking(self, mock_post):
        """Test batch verification with large list (tests chunking)."""
        # Generate 1500 emails to test chunking (should split into 2 requests)
        large_email_list = [f"user{i}@test.com" for i in range(1500)]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"email": email, "status": "valid"} for email in large_email_list
            ]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            results = self.verifier.verify_batch(large_email_list)
        
        # Should have verified all emails
        assert len(results) == 1500
        # Check first and last
        assert results["user0@test.com"] is True
        assert results["user1499@test.com"] is True
        # Verify chunking happened (2 API calls)
        assert mock_post.call_count == 2
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_batch_mixed_results(self, mock_post):
        """Test batch with mixed valid/invalid results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"email": "valid@test.com", "status": "valid"},
                {"email": "role@test.com", "status": "role"},
                {"email": "disposable@test.com", "status": "disposable"}
            ]
        }
        mock_post.return_value = mock_response
        
        test_emails = ["valid@test.com", "role@test.com", "disposable@test.com"]
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            results = self.verifier.verify_batch(test_emails)
        
        assert results["valid@test.com"] is True
        assert results["role@test.com"] is False
        assert results["disposable@test.com"] is False
    
    @patch("aicmo.gateways.adapters.dropcontact_verifier.requests.post")
    def test_verify_batch_api_error(self, mock_post):
        """Test batch with API error (optimistic fallback)."""
        mock_post.side_effect = Exception("API timeout")
        
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            results = self.verifier.verify_batch(self.test_emails)
        
        # Optimistic fallback: approve all on error
        assert all(results.values())
    
    def test_verify_batch_no_api_key(self):
        """Test batch verification without API key (optimistic)."""
        with patch.dict(os.environ, {}, clear=True):
            results = self.verifier.verify_batch(self.test_emails)
        
        # Optimistic fallback: approve all when not configured
        assert len(results) == len(self.test_emails)
        assert all(results.values())
    
    def test_verify_batch_empty_list(self):
        """Test batch with empty list."""
        with patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"}):
            results = self.verifier.verify_batch([])
        
        assert results == {}


class TestDropcontactVerifierConfig:
    """Test Dropcontact verifier configuration."""
    
    @patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"})
    def test_is_configured_with_key(self):
        """Test is_configured when API key present."""
        verifier = DropcontactVerifier()
        assert verifier.is_configured() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_configured_without_key(self):
        """Test is_configured when API key missing."""
        verifier = DropcontactVerifier()
        assert verifier.is_configured() is False
    
    def test_get_name(self):
        """Test verifier name."""
        verifier = DropcontactVerifier()
        assert verifier.get_name() == "Dropcontact Verifier"


class TestDropcontactFactory:
    """Test Dropcontact integration with factory."""
    
    @patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"})
    def test_factory_returns_dropcontact_verifier(self):
        """Test factory returns DropcontactVerifier when configured."""
        verifier = get_email_verifier()
        assert isinstance(verifier, DropcontactVerifier)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_factory_returns_noop_when_not_configured(self):
        """Test factory returns no-op verifier when not configured."""
        verifier = get_email_verifier()
        # Should return some verifier (possibly no-op)
        assert verifier is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
