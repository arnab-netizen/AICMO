"""
Tests for Apollo Lead Enricher integration.

Tests the real Apollo API implementation including:
- Fetch from Apollo with mocked requests
- Batch enrichment with contact mapping
- Error handling and fallback behavior
- Factory integration for real vs no-op mode
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime

from aicmo.gateways.adapters.apollo_enricher import ApolloEnricher
from aicmo.gateways.factory import get_lead_enricher


class TestApolloEnricherFetch:
    """Test Apollo lead fetching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.enricher = ApolloEnricher()
        self.test_email = "test@example.com"
        self.test_domain = "example.com"
    
    @patch("aicmo.gateways.adapters.apollo_enricher.requests.post")
    def test_fetch_from_apollo_success(self, mock_post):
        """Test successful fetch from Apollo API."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "people": [
                {
                    "email": self.test_email,
                    "first_name": "John",
                    "last_name": "Doe",
                    "title": "Marketing Manager",
                    "organization_name": "Acme Inc",
                    "linkedin_url": "https://linkedin.com/in/johndoe",
                    "phone_number": "+1-555-0100",
                    "industry": "Technology",
                    "seniority_level": "manager"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            result = self.enricher.fetch_from_apollo(self.test_email)
        
        # Assert
        assert result is not None
        assert result["email"] == self.test_email
        assert result["company"] == "Acme Inc"
        assert result["job_title"] == "Marketing Manager"
        assert result["linkedin_url"] == "https://linkedin.com/in/johndoe"
        assert result["phone"] == "+1-555-0100"
        assert result["industry"] == "Technology"
        assert result["seniority"] == "manager"
    
    @patch("aicmo.gateways.adapters.apollo_enricher.requests.post")
    def test_fetch_from_apollo_no_results(self, mock_post):
        """Test Apollo API with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"people": []}
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            result = self.enricher.fetch_from_apollo(self.test_email)
        
        assert result is None
    
    @patch("aicmo.gateways.adapters.apollo_enricher.requests.post")
    def test_fetch_from_apollo_api_error(self, mock_post):
        """Test Apollo API error handling."""
        mock_post.side_effect = Exception("Network error")
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            result = self.enricher.fetch_from_apollo(self.test_email)
        
        # Should return None, not crash
        assert result is None
    
    def test_fetch_from_apollo_no_api_key(self):
        """Test fetch when API key not configured."""
        # Clear the API key
        with patch.dict(os.environ, {}, clear=True):
            result = self.enricher.fetch_from_apollo(self.test_email)
        
        # Should return None (safe no-op)
        assert result is None


class TestApolloEnricherBatch:
    """Test Apollo batch enrichment functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.enricher = ApolloEnricher()
        self.test_emails = [
            "alice@acme.com",
            "bob@acme.com",
            "charlie@acme.com"
        ]
    
    @patch("aicmo.gateways.adapters.apollo_enricher.requests.post")
    def test_enrich_batch_success(self, mock_post):
        """Test successful batch enrichment."""
        # Mock response with multiple contacts
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "people": [
                {
                    "email": "alice@acme.com",
                    "first_name": "Alice",
                    "title": "VP Sales",
                    "organization_name": "Acme Inc",
                    "linkedin_url": "https://linkedin.com/in/alice",
                    "phone_number": "+1-555-0101",
                    "industry": "SaaS",
                    "seniority_level": "executive"
                },
                {
                    "email": "bob@acme.com",
                    "first_name": "Bob",
                    "title": "Developer",
                    "organization_name": "Acme Inc",
                    "linkedin_url": "https://linkedin.com/in/bob",
                    "phone_number": "+1-555-0102",
                    "industry": "SaaS",
                    "seniority_level": "individual_contributor"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            results = self.enricher.enrich_batch(self.test_emails)
        
        # Assert
        assert len(results) >= 2
        assert results[0]["email"] == "alice@acme.com"
        assert results[0]["job_title"] == "VP Sales"
        assert results[1]["email"] == "bob@acme.com"
        assert results[1]["job_title"] == "Developer"
    
    @patch("aicmo.gateways.adapters.apollo_enricher.requests.post")
    def test_enrich_batch_with_failures(self, mock_post):
        """Test batch enrichment with partial failures."""
        # First call succeeds, second call fails
        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            "people": [
                {
                    "email": "alice@acme.com",
                    "first_name": "Alice",
                    "title": "Manager"
                }
            ]
        }
        
        mock_response_2 = Mock()
        mock_response_2.status_code = 429  # Rate limited
        
        mock_post.side_effect = [mock_response_1, Exception("Rate limited")]
        
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            results = self.enricher.enrich_batch(self.test_emails)
        
        # Should have at least the first result
        assert len(results) >= 1
        assert results[0]["email"] == "alice@acme.com"
    
    def test_enrich_batch_empty_list(self):
        """Test batch enrichment with empty list."""
        with patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"}):
            results = self.enricher.enrich_batch([])
        
        assert results == []
    
    def test_enrich_batch_no_api_key(self):
        """Test batch enrichment without API key."""
        with patch.dict(os.environ, {}, clear=True):
            results = self.enricher.enrich_batch(self.test_emails)
        
        # Should return empty list (safe no-op)
        assert results == []


class TestApolloEnricherConfig:
    """Test Apollo enricher configuration."""
    
    @patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"})
    def test_is_configured_with_key(self):
        """Test is_configured returns True when API key present."""
        enricher = ApolloEnricher()
        assert enricher.is_configured() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_configured_without_key(self):
        """Test is_configured returns False when API key missing."""
        enricher = ApolloEnricher()
        assert enricher.is_configured() is False
    
    def test_get_name(self):
        """Test enricher name."""
        enricher = ApolloEnricher()
        assert enricher.get_name() == "Apollo Enricher"


class TestApolloFactory:
    """Test Apollo integration with factory."""
    
    @patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"})
    def test_factory_returns_apollo_enricher(self):
        """Test factory returns ApolloEnricher when configured."""
        enricher = get_lead_enricher()
        assert isinstance(enricher, ApolloEnricher)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_factory_returns_noop_when_not_configured(self):
        """Test factory returns no-op enricher when not configured."""
        enricher = get_lead_enricher()
        # Should return some enricher (possibly no-op)
        assert enricher is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
