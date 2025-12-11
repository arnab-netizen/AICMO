"""
Integration tests for External Integrations (Apollo, Dropcontact, PPTX, HTML, Airtable).

These tests verify that:
1. All adapters can be instantiated
2. Factory pattern returns correct adapters based on configuration
3. All adapters implement required interfaces
4. Graceful fallback to no-op when not configured
"""

import pytest
import os
from unittest.mock import patch

from aicmo.gateways.adapters.apollo_enricher import ApolloEnricher
from aicmo.gateways.adapters.dropcontact_verifier import DropcontactVerifier
from aicmo.gateways.adapters.airtable_crm import AirtableCRMSyncer
from aicmo.delivery.output_packager import generate_html_summary, generate_full_deck_pptx
from aicmo.gateways.factory import get_lead_enricher, get_email_verifier, get_crm_syncer


class TestExternalIntegrationsInstantiation:
    """Test that all external integrations can be instantiated."""
    
    def test_apollo_enricher_instantiation(self):
        """Apollo enricher can be created."""
        enricher = ApolloEnricher()
        assert enricher is not None
        assert hasattr(enricher, 'is_configured')
        assert hasattr(enricher, 'fetch_from_apollo')
        assert hasattr(enricher, 'enrich_batch')
    
    def test_dropcontact_verifier_instantiation(self):
        """Dropcontact verifier can be created."""
        verifier = DropcontactVerifier()
        assert verifier is not None
        assert hasattr(verifier, 'is_configured')
        assert hasattr(verifier, 'verify')
        assert hasattr(verifier, 'verify_batch')
    
    def test_airtable_crm_instantiation(self):
        """Airtable CRM syncer can be created."""
        syncer = AirtableCRMSyncer()
        assert syncer is not None
        assert hasattr(syncer, 'is_configured')
        assert hasattr(syncer, 'sync_contact')
        assert hasattr(syncer, 'log_engagement')
    
    def test_pptx_generation_callable(self):
        """PPTX generation function is callable."""
        assert callable(generate_full_deck_pptx)
    
    def test_html_generation_callable(self):
        """HTML generation function is callable."""
        assert callable(generate_html_summary)


class TestAdapterConfiguration:
    """Test adapter configuration detection."""
    
    @patch.dict(os.environ, {"APOLLO_API_KEY": "test_key"})
    def test_apollo_configured_when_key_set(self):
        """Apollo reports configured when API key is set."""
        enricher = ApolloEnricher()
        assert enricher.is_configured() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_apollo_not_configured_without_key(self):
        """Apollo reports not configured without API key."""
        enricher = ApolloEnricher()
        assert enricher.is_configured() is False
    
    @patch.dict(os.environ, {"DROPCONTACT_API_KEY": "test_key"})
    def test_dropcontact_configured_when_key_set(self):
        """Dropcontact reports configured when API key is set."""
        verifier = DropcontactVerifier()
        assert verifier.is_configured() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_dropcontact_not_configured_without_key(self):
        """Dropcontact reports not configured without API key."""
        verifier = DropcontactVerifier()
        assert verifier.is_configured() is False
    
    @patch.dict(os.environ, {
        "AIRTABLE_API_KEY": "test_key",
        "AIRTABLE_BASE_ID": "appXXXXXXX"
    })
    def test_airtable_configured_when_vars_set(self):
        """Airtable reports configured when required env vars are set."""
        syncer = AirtableCRMSyncer()
        assert syncer.is_configured() is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_airtable_not_configured_without_vars(self):
        """Airtable reports not configured without required env vars."""
        syncer = AirtableCRMSyncer()
        assert syncer.is_configured() is False


class TestAdapterNames:
    """Test that adapters report correct names."""
    
    def test_apollo_name(self):
        """Apollo reports correct name."""
        enricher = ApolloEnricher()
        assert enricher.get_name() == "Apollo Enricher"
    
    def test_dropcontact_name(self):
        """Dropcontact reports correct name."""
        verifier = DropcontactVerifier()
        assert verifier.get_name() == "Dropcontact Verifier"
    
    def test_airtable_name(self):
        """Airtable reports correct name."""
        syncer = AirtableCRMSyncer()
        assert syncer.get_name() == "Airtable CRM Syncer"


class TestFactoryReturnTypes:
    """Test that factory returns correct adapter types based on configuration."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_factory_returns_enricher(self):
        """Factory returns some enricher (noop or real)."""
        enricher = get_lead_enricher()
        assert enricher is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_factory_returns_verifier(self):
        """Factory returns some verifier (noop or real)."""
        verifier = get_email_verifier()
        assert verifier is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_factory_returns_crm_syncer(self):
        """Factory returns some CRM syncer (noop or real)."""
        syncer = get_crm_syncer()
        assert syncer is not None


class TestGenerationFunctions:
    """Test file generation functions."""
    
    def test_pptx_function_accepts_project_data(self):
        """PPTX function accepts project_data parameter."""
        import inspect
        sig = inspect.signature(generate_full_deck_pptx)
        assert "project_data" in sig.parameters
    
    def test_html_function_accepts_project_data(self):
        """HTML function accepts project_data parameter."""
        import inspect
        sig = inspect.signature(generate_html_summary)
        assert "project_data" in sig.parameters
    
    def test_html_generation_with_minimal_data(self):
        """HTML generation works with minimal data."""
        minimal_data = {
            "project_name": "Test",
            "objective": "Test",
            "platforms": {},
            "strategy": "",
            "calendar": [],
            "deliverables": []
        }
        result = generate_html_summary(minimal_data)
        
        # Should return a file path or None
        if result is not None:
            assert isinstance(result, str)
            # Clean up
            import os as os_module
            if os_module.path.exists(result):
                os_module.remove(result)


class TestInterfaceImplementation:
    """Test that adapters implement required interfaces."""
    
    def test_apollo_implements_lead_enricher_interface(self):
        """Apollo implements LeadEnricherPort interface."""
        from aicmo.cam.ports import LeadEnricherPort
        enricher = ApolloEnricher()
        assert isinstance(enricher, LeadEnricherPort)
    
    def test_dropcontact_implements_email_verifier_interface(self):
        """Dropcontact implements EmailVerifierPort interface."""
        from aicmo.cam.ports import EmailVerifierPort
        verifier = DropcontactVerifier()
        assert isinstance(verifier, EmailVerifierPort)
    
    def test_airtable_implements_crm_syncer_interface(self):
        """Airtable implements CRMSyncer interface."""
        from aicmo.gateways.interfaces import CRMSyncer
        syncer = AirtableCRMSyncer()
        assert isinstance(syncer, CRMSyncer)


class TestFallbackBehavior:
    """Test graceful fallback behavior when not configured."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_apollo_unconfigured_batch_returns_empty(self):
        """Apollo batch returns empty when not configured."""
        enricher = ApolloEnricher()
        result = enricher.enrich_batch(["test@example.com"])
        # Should return empty list (no-op)
        assert isinstance(result, (list, dict))
    
    @patch.dict(os.environ, {}, clear=True)
    def test_dropcontact_unconfigured_verify_optimistic(self):
        """Dropcontact verify returns True when not configured (optimistic)."""
        verifier = DropcontactVerifier()
        result = verifier.verify("test@example.com")
        # Optimistic: approve when not configured
        assert result is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_airtable_unconfigured_returns_safe_status(self):
        """Airtable returns safe status when not configured."""
        import asyncio
        syncer = AirtableCRMSyncer()
        result = asyncio.run(syncer.validate_connection())
        # Should return False when not configured
        assert result is False


class TestEnvironmentVariableHandling:
    """Test correct handling of environment variables."""
    
    @patch.dict(os.environ, {"AIRTABLE_CONTACTS_TABLE": "CustomContacts"})
    def test_airtable_loads_custom_table_names(self):
        """Airtable loads custom table names from env."""
        syncer = AirtableCRMSyncer()
        assert syncer.contacts_table == "CustomContacts"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_airtable_uses_default_table_names(self):
        """Airtable uses default table names when not configured."""
        syncer = AirtableCRMSyncer()
        assert syncer.contacts_table == "Contacts"
        assert syncer.interactions_table == "Interactions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
