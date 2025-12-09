"""
Lead Enricher Port.

Interface for enriching lead data with additional information.
Implementations may connect to Apollo, Dropcontact, clearbit, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..domain import Lead


class LeadEnricherPort(ABC):
    """
    Abstract port for enriching lead data with additional information.
    
    Takes a basic lead and adds enrichment data like company info,
    job history, social profiles, firmographics, etc.
    """
    
    @abstractmethod
    def enrich(self, lead: Lead) -> Lead:
        """
        Enrich a lead with additional data.
        
        Adds enrichment_data field to the lead with extra information.
        If enrichment fails or is not available, returns lead unchanged.
        
        Args:
            lead: Lead to enrich
            
        Returns:
            Lead with enrichment_data populated (if successful)
            
        Raises:
            Exception: On API errors, network issues, etc.
                       Implementations should log and handle gracefully.
        """
        pass
    
    @abstractmethod
    def enrich_batch(self, leads: list[Lead]) -> list[Lead]:
        """
        Enrich multiple leads efficiently (batch mode).
        
        Some enrichers support batch APIs for better rate limiting.
        Falls back to per-lead enrichment if not supported.
        
        Args:
            leads: List of leads to enrich
            
        Returns:
            List of enriched leads
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if this enricher is properly configured.
        
        Returns:
            True if ready to use, False otherwise
            (e.g. API key is set, credentials valid)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get human-readable name of this enricher.
        
        Returns:
            Name like "Apollo", "Dropcontact", "Clearbit", etc.
        """
        pass
