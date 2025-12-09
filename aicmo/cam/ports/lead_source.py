"""
Lead Source Port.

Interface for finding and fetching new leads from various sources.
Implementations may connect to Apollo, LinkedIn, CSV files, etc.
"""

from abc import ABC, abstractmethod
from typing import List

from ..domain import Lead, Campaign


class LeadSourcePort(ABC):
    """
    Abstract port for discovering and fetching new leads.
    
    Each adapter (Apollo, CSV, LinkedIn, etc.) implements this interface
    to provide a consistent way to fetch leads.
    """
    
    @abstractmethod
    def fetch_new_leads(self, campaign: Campaign, max_leads: int = 50) -> List[Lead]:
        """
        Fetch new leads matching campaign criteria.
        
        Args:
            campaign: Campaign to find leads for
            max_leads: Maximum number of leads to fetch
            
        Returns:
            List of Lead objects ready for outreach
            
        Raises:
            Exception: On API errors, network issues, etc.
                       Implementations should log and handle gracefully.
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if this lead source is properly configured.
        
        Returns:
            True if ready to use, False otherwise
            (e.g. API key is set, credentials valid)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get human-readable name of this lead source.
        
        Returns:
            Name like "Apollo", "LinkedIn", "CSV File", etc.
        """
        pass
