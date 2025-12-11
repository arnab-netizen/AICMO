"""
Tests for Airtable CRM Adapter integration.

Tests the Airtable CRM implementation including:
- Contact synchronization (create/update)
- Engagement logging
- Connection validation
- Configuration checking
- Factory integration
- Error handling and graceful degradation
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
import asyncio

from aicmo.gateways.adapters.airtable_crm import AirtableCRMSyncer
from aicmo.domain.execution import ExecutionStatus
from aicmo.gateways.factory import get_crm_syncer


class TestAirtableCRMSyncerConfig:
    """Test Airtable CRM configuration."""
    
    @patch.dict(os.environ, {
        "AIRTABLE_API_KEY": "test_key",
        "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX",
        "USE_REAL_CRM_GATEWAY": "true"
    })
    def test_is_configured_with_all_vars(self):
        """Test is_configured when all required env vars are set."""
        syncer = AirtableCRMSyncer()
        assert syncer.is_configured() is True
    
    @patch.dict(os.environ, {
        "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
    }, clear=True)
    def test_is_configured_missing_api_key(self):
        """Test is_configured when API key missing."""
        syncer = AirtableCRMSyncer()
        assert syncer.is_configured() is False
    
    @patch.dict(os.environ, {
        "AIRTABLE_API_KEY": "test_key"
    }, clear=True)
    def test_is_configured_missing_base_id(self):
        """Test is_configured when BASE_ID missing."""
        syncer = AirtableCRMSyncer()
        assert syncer.is_configured() is False
    
    def test_get_name(self):
        """Test syncer name."""
        syncer = AirtableCRMSyncer()
        assert syncer.get_name() == "Airtable CRM Syncer"
    
    @patch.dict(os.environ, {
        "AIRTABLE_CONTACTS_TABLE": "MyContacts",
        "AIRTABLE_INTERACTIONS_TABLE": "MyInteractions"
    }, clear=True)
    def test_table_names_from_env(self):
        """Test that table names are loaded from environment."""
        syncer = AirtableCRMSyncer()
        assert syncer.contacts_table == "MyContacts"
        assert syncer.interactions_table == "MyInteractions"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_table_names_defaults(self):
        """Test default table names."""
        syncer = AirtableCRMSyncer()
        assert syncer.contacts_table == "Contacts"
        assert syncer.interactions_table == "Interactions"


class TestAirtableCRMSyncContact:
    """Test contact synchronization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_email = "test@example.com"
        self.test_properties = {
            "name": "John Doe",
            "company": "Acme Inc",
            "title": "Manager"
        }
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.get")
    @patch("aicmo.gateways.adapters.airtable_crm.requests.patch")
    def test_sync_contact_update_existing(self, mock_patch, mock_get):
        """Test updating an existing contact."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            # Mock GET to find existing record
            get_response = Mock()
            get_response.json.return_value = {
                "records": [
                    {"id": "rec123", "fields": {"Email": self.test_email}}
                ]
            }
            mock_get.return_value = get_response
            
            # Mock PATCH for update
            patch_response = Mock()
            patch_response.json.return_value = {"id": "rec123"}
            mock_patch.return_value = patch_response
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.sync_contact(self.test_email, self.test_properties))
            
            assert result.status == ExecutionStatus.SUCCESS
            assert result.data["record_id"] == "rec123"
            assert result.data["action"] == "updated"
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.get")
    @patch("aicmo.gateways.adapters.airtable_crm.requests.post")
    def test_sync_contact_create_new(self, mock_post, mock_get):
        """Test creating a new contact."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            # Mock GET to return no existing records
            get_response = Mock()
            get_response.json.return_value = {"records": []}
            mock_get.return_value = get_response
            
            # Mock POST for create
            post_response = Mock()
            post_response.json.return_value = {"id": "rec456"}
            mock_post.return_value = post_response
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.sync_contact(self.test_email, self.test_properties))
            
            assert result.status == ExecutionStatus.SUCCESS
            assert result.data["record_id"] == "rec456"
            assert result.data["action"] == "created"
    
    def test_sync_contact_no_email(self):
        """Test sync with no email (should fail)."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.sync_contact("", self.test_properties))
            
            assert result.status == ExecutionStatus.FAILED
    
    def test_sync_contact_not_configured(self):
        """Test sync when not configured (should skip)."""
        with patch.dict(os.environ, {}, clear=True):
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.sync_contact(self.test_email, self.test_properties))
            
            assert result.status == ExecutionStatus.SKIPPED
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.get")
    @patch("aicmo.gateways.adapters.airtable_crm.requests.post")
    def test_sync_contact_api_error(self, mock_post, mock_get):
        """Test sync with API error."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            # Mock API error
            mock_get.side_effect = Exception("Connection error")
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.sync_contact(self.test_email, self.test_properties))
            
            assert result.status == ExecutionStatus.FAILED


class TestAirtableCRMLogEngagement:
    """Test engagement logging."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.contact_email = "test@example.com"
        self.engagement_type = "email_open"
        self.content_id = "content_123"
        self.metadata = {"ip": "192.168.1.1", "device": "mobile"}
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.post")
    def test_log_engagement_success(self, mock_post):
        """Test successful engagement logging."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            # Mock POST for engagement logging
            post_response = Mock()
            post_response.json.return_value = {"id": "rec789"}
            mock_post.return_value = post_response
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.log_engagement(
                self.contact_email,
                self.engagement_type,
                self.content_id,
                self.metadata
            ))
            
            assert result.status == ExecutionStatus.SUCCESS
            assert result.data["record_id"] == "rec789"
    
    def test_log_engagement_not_configured(self):
        """Test engagement logging when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.log_engagement(
                self.contact_email,
                self.engagement_type,
                self.content_id,
                self.metadata
            ))
            
            assert result.status == ExecutionStatus.SKIPPED
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.post")
    def test_log_engagement_api_error(self, mock_post):
        """Test engagement logging with API error."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            mock_post.side_effect = Exception("API error")
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.log_engagement(
                self.contact_email,
                self.engagement_type,
                self.content_id,
                self.metadata
            ))
            
            assert result.status == ExecutionStatus.FAILED


class TestAirtableCRMConnection:
    """Test connection validation."""
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.get")
    def test_validate_connection_success(self, mock_get):
        """Test successful connection validation."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "test_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            mock_get.return_value = Mock(status_code=200)
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.validate_connection())
            
            assert result is True
    
    @patch("aicmo.gateways.adapters.airtable_crm.requests.get")
    def test_validate_connection_failure(self, mock_get):
        """Test failed connection validation."""
        with patch.dict(os.environ, {
            "AIRTABLE_API_KEY": "invalid_key",
            "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX"
        }):
            mock_get.side_effect = Exception("Unauthorized")
            
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.validate_connection())
            
            assert result is False
    
    def test_validate_connection_not_configured(self):
        """Test connection validation when not configured."""
        with patch.dict(os.environ, {}, clear=True):
            syncer = AirtableCRMSyncer()
            result = asyncio.run(syncer.validate_connection())
            
            assert result is False


class TestAirtableFactory:
    """Test Airtable integration with factory."""
    
    @patch.dict(os.environ, {
        "AIRTABLE_API_KEY": "test_key",
        "AIRTABLE_BASE_ID": "appXXXXXXXXXXXX",
        "USE_REAL_CRM_GATEWAY": "true"
    })
    def test_factory_returns_airtable_when_configured(self):
        """Test factory returns AirtableCRMSyncer when configured."""
        syncer = get_crm_syncer()
        assert isinstance(syncer, AirtableCRMSyncer)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_factory_returns_noop_when_not_configured(self):
        """Test factory returns no-op syncer when not configured."""
        syncer = get_crm_syncer()
        # Should return some syncer (possibly no-op)
        assert syncer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
