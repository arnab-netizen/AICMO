"""
Tests for CAM Ports and Adapters.

Phase CAM-2: Test port interfaces and adapter implementations.
"""

import unittest
from unittest.mock import patch, MagicMock

from aicmo.cam.domain import Lead, Campaign, LeadSource, LeadStatus
from aicmo.cam.ports import LeadSourcePort, LeadEnricherPort, EmailVerifierPort
from aicmo.gateways.adapters.cam_noop import (
    NoOpLeadSource,
    NoOpLeadEnricher,
    NoOpEmailVerifier,
)
from aicmo.gateways.adapters.apollo_enricher import ApolloEnricher
from aicmo.gateways.adapters.dropcontact_verifier import DropcontactVerifier
from aicmo.gateways.adapters.make_webhook import MakeWebhookAdapter


class TestNoOpLeadSource(unittest.TestCase):
    """Test no-op lead source adapter."""
    
    def setUp(self):
        self.source = NoOpLeadSource()
        self.campaign = Campaign(id=1, name="Test Campaign")
    
    def test_fetch_new_leads_returns_empty_list(self):
        """No-op should return empty list."""
        leads = self.source.fetch_new_leads(self.campaign, max_leads=10)
        self.assertEqual(leads, [])
    
    def test_is_configured_returns_false(self):
        """No-op is never configured."""
        self.assertFalse(self.source.is_configured())
    
    def test_get_name(self):
        """Should return human-readable name."""
        name = self.source.get_name()
        self.assertIn("No-op", name)


class TestNoOpLeadEnricher(unittest.TestCase):
    """Test no-op lead enricher adapter."""
    
    def setUp(self):
        self.enricher = NoOpLeadEnricher()
        self.lead = Lead(
            id=1,
            name="John Doe",
            email="john@example.com",
            company="Acme Corp",
        )
    
    def test_enrich_returns_lead_unchanged(self):
        """No-op should return lead without modification."""
        enriched = self.enricher.enrich(self.lead)
        self.assertEqual(enriched.id, self.lead.id)
        self.assertEqual(enriched.email, self.lead.email)
        self.assertIsNone(enriched.enrichment_data)
    
    def test_enrich_batch_returns_leads_unchanged(self):
        """No-op batch should return leads unchanged."""
        leads = [self.lead, self.lead]
        enriched = self.enricher.enrich_batch(leads)
        self.assertEqual(len(enriched), 2)
        self.assertEqual(enriched[0].email, self.lead.email)
    
    def test_is_configured_returns_false(self):
        """No-op is never configured."""
        self.assertFalse(self.enricher.is_configured())


class TestNoOpEmailVerifier(unittest.TestCase):
    """Test no-op email verifier adapter."""
    
    def setUp(self):
        self.verifier = NoOpEmailVerifier()
    
    def test_verify_returns_true(self):
        """No-op optimistic: all emails valid."""
        result = self.verifier.verify("test@example.com")
        self.assertTrue(result)
    
    def test_verify_batch_returns_all_true(self):
        """No-op batch: all emails valid."""
        emails = ["test1@example.com", "test2@example.com"]
        results = self.verifier.verify_batch(emails)
        self.assertEqual(len(results), 2)
        for email in emails:
            self.assertTrue(results[email])
    
    def test_is_configured_returns_false(self):
        """No-op is never configured."""
        self.assertFalse(self.verifier.is_configured())


class TestApolloEnricher(unittest.TestCase):
    """Test Apollo enricher adapter."""
    
    def setUp(self):
        self.enricher = ApolloEnricher()
        self.lead = Lead(
            id=1,
            name="Jane Smith",
            email="jane@techcompany.com",
            company="Tech Co",
        )
    
    @patch.dict('os.environ', {}, clear=False)
    def test_is_configured_false_without_api_key(self):
        """Apollo unconfigured without API key."""
        enricher = ApolloEnricher()
        self.assertFalse(enricher.is_configured())
    
    @patch.dict('os.environ', {'APOLLO_API_KEY': 'test-key'})
    def test_is_configured_true_with_api_key(self):
        """Apollo configured with API key."""
        enricher = ApolloEnricher()
        self.assertTrue(enricher.is_configured())
    
    def test_get_name(self):
        """Should return human-readable name."""
        name = self.enricher.get_name()
        self.assertIn("Apollo", name)
    
    def test_enrich_without_email_returns_lead_unchanged(self):
        """Should skip enrichment if no email."""
        lead_no_email = Lead(id=1, name="Test", company="Test Co")
        result = self.enricher.enrich(lead_no_email)
        self.assertEqual(result.id, lead_no_email.id)


class TestDropcontactVerifier(unittest.TestCase):
    """Test Dropcontact email verifier adapter."""
    
    def setUp(self):
        self.verifier = DropcontactVerifier()
    
    @patch.dict('os.environ', {}, clear=False)
    def test_is_configured_false_without_api_key(self):
        """Dropcontact unconfigured without API key."""
        verifier = DropcontactVerifier()
        self.assertFalse(verifier.is_configured())
    
    @patch.dict('os.environ', {'DROPCONTACT_API_KEY': 'test-key'})
    def test_is_configured_true_with_api_key(self):
        """Dropcontact configured with API key."""
        verifier = DropcontactVerifier()
        self.assertTrue(verifier.is_configured())
    
    def test_get_name(self):
        """Should return human-readable name."""
        name = self.verifier.get_name()
        self.assertIn("Dropcontact", name)
    
    def test_verify_defaults_to_true_when_not_configured(self):
        """Optimistic: approve emails when not configured."""
        result = self.verifier.verify("test@example.com")
        self.assertTrue(result)
    
    def test_verify_batch_defaults_to_all_true(self):
        """Optimistic batch: approve all when not configured."""
        emails = ["test1@example.com", "test2@example.com"]
        results = self.verifier.verify_batch(emails)
        for email in emails:
            self.assertTrue(results[email])


class TestMakeWebhookAdapter(unittest.TestCase):
    """Test Make.com webhook adapter."""
    
    def setUp(self):
        self.adapter = MakeWebhookAdapter()
    
    @patch.dict('os.environ', {}, clear=False)
    def test_is_configured_false_without_webhook_url(self):
        """Not configured without webhook URL."""
        adapter = MakeWebhookAdapter()
        self.assertFalse(adapter.is_configured())
    
    @patch.dict('os.environ', {'MAKE_WEBHOOK_URL': 'https://hook.make.com/test'})
    def test_is_configured_true_with_webhook_url(self):
        """Configured with webhook URL."""
        adapter = MakeWebhookAdapter()
        self.assertTrue(adapter.is_configured())
    
    def test_get_name(self):
        """Should return human-readable name."""
        name = self.adapter.get_name()
        self.assertIn("Make", name)
    
    @patch('aicmo.gateways.adapters.make_webhook.requests.post')
    def test_send_event_success(self, mock_post):
        """Should send event successfully."""
        mock_post.return_value.status_code = 200
        
        with patch.dict('os.environ', {'MAKE_WEBHOOK_URL': 'https://hook.make.com/test'}):
            adapter = MakeWebhookAdapter()
            result = adapter.send_event("TestEvent", {"key": "value"})
            self.assertTrue(result)
            mock_post.assert_called_once()
    
    @patch('aicmo.gateways.adapters.make_webhook.requests.post')
    def test_send_event_network_error_returns_false(self, mock_post):
        """Should handle network errors gracefully."""
        mock_post.side_effect = Exception("Network error")
        
        with patch.dict('os.environ', {'MAKE_WEBHOOK_URL': 'https://hook.make.com/test'}):
            adapter = MakeWebhookAdapter()
            result = adapter.send_event("TestEvent", {"key": "value"})
            self.assertFalse(result)


class TestGatewayFactory(unittest.TestCase):
    """Test gateway factory CAM functions."""
    
    def test_get_lead_source_returns_instance(self):
        """Factory should return lead source adapter."""
        from aicmo.gateways.factory import get_lead_source
        source = get_lead_source()
        self.assertIsNotNone(source)
        # Should be no-op by default (no APOLLO_API_KEY)
        self.assertFalse(source.is_configured())
    
    def test_get_lead_enricher_returns_instance(self):
        """Factory should return lead enricher adapter."""
        from aicmo.gateways.factory import get_lead_enricher
        enricher = get_lead_enricher()
        self.assertIsNotNone(enricher)
        # Should be no-op by default (no APOLLO_API_KEY)
        self.assertFalse(enricher.is_configured())
    
    def test_get_email_verifier_returns_instance(self):
        """Factory should return email verifier adapter."""
        from aicmo.gateways.factory import get_email_verifier
        verifier = get_email_verifier()
        self.assertIsNotNone(verifier)
        # Should be no-op by default (no DROPCONTACT_API_KEY)
        self.assertFalse(verifier.is_configured())
    
    def test_get_make_webhook_returns_instance(self):
        """Factory should return Make.com webhook adapter."""
        from aicmo.gateways.factory import get_make_webhook
        adapter = get_make_webhook()
        self.assertIsNotNone(adapter)


if __name__ == "__main__":
    unittest.main()
