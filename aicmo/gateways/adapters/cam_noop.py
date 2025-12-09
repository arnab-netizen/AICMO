"""
No-op Adapters for CAM Ports.

Safe fallback implementations when real adapters aren't configured.
All return sensible defaults without making external calls.
"""

import logging
from typing import List, Dict

from aicmo.cam.domain import Lead, Campaign
from aicmo.cam.ports import LeadSourcePort, LeadEnricherPort, EmailVerifierPort

logger = logging.getLogger(__name__)


class NoOpLeadSource(LeadSourcePort):
    """
    No-op lead source that returns empty list.
    
    Used when no external lead source is configured.
    """
    
    def fetch_new_leads(self, campaign: Campaign, max_leads: int = 50) -> List[Lead]:
        """Return empty list (no leads available)."""
        logger.debug(f"NoOpLeadSource.fetch_new_leads(): No leads available")
        return []
    
    def is_configured(self) -> bool:
        """Always return False (not configured)."""
        return False
    
    def get_name(self) -> str:
        """Return name."""
        return "No-op Lead Source"


class NoOpLeadEnricher(LeadEnricherPort):
    """
    No-op enricher that returns leads unchanged.
    
    Used when no external enricher is configured.
    """
    
    def enrich(self, lead: Lead) -> Lead:
        """Return lead unchanged."""
        logger.debug(f"NoOpLeadEnricher.enrich(): No enrichment available for {lead.name}")
        return lead
    
    def enrich_batch(self, leads: list[Lead]) -> list[Lead]:
        """Return leads unchanged."""
        logger.debug(f"NoOpLeadEnricher.enrich_batch(): No enrichment for {len(leads)} leads")
        return leads
    
    def is_configured(self) -> bool:
        """Always return False (not configured)."""
        return False
    
    def get_name(self) -> str:
        """Return name."""
        return "No-op Lead Enricher"


class NoOpEmailVerifier(EmailVerifierPort):
    """
    No-op verifier that approves all emails.
    
    Used when no external verifier is configured.
    Optimistic strategy: assume all emails are valid.
    """
    
    def verify(self, email: str) -> bool:
        """Return True (assume valid)."""
        logger.debug(f"NoOpEmailVerifier.verify(): Approving email {email}")
        return True
    
    def verify_batch(self, emails: list[str]) -> Dict[str, bool]:
        """Return all emails as valid."""
        logger.debug(f"NoOpEmailVerifier.verify_batch(): Approving {len(emails)} emails")
        return {email: True for email in emails}
    
    def is_configured(self) -> bool:
        """Always return False (not configured)."""
        return False
    
    def get_name(self) -> str:
        """Return name."""
        return "No-op Email Verifier"
