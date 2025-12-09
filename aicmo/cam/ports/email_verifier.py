"""
Email Verifier Port.

Interface for verifying email addresses before outreach.
Implementations may connect to Dropcontact, NeverBounce, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict

from ..domain import Lead


class EmailVerifierPort(ABC):
    """
    Abstract port for verifying email address validity.
    
    Takes a lead email and checks if it's real, deliverable, etc.
    Helps reduce bounce rates and avoid spam traps.
    """
    
    @abstractmethod
    def verify(self, email: str) -> bool:
        """
        Verify if an email address is valid and deliverable.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if email appears valid/deliverable, False otherwise
            
        Raises:
            Exception: On API errors, network issues, etc.
                       Implementations should log and handle gracefully.
        """
        pass
    
    @abstractmethod
    def verify_batch(self, emails: list[str]) -> Dict[str, bool]:
        """
        Verify multiple email addresses efficiently (batch mode).
        
        Some verifiers support batch APIs for better rate limiting.
        Falls back to per-email verification if not supported.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict mapping email -> validity (True/False)
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if this verifier is properly configured.
        
        Returns:
            True if ready to use, False otherwise
            (e.g. API key is set, credentials valid)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get human-readable name of this verifier.
        
        Returns:
            Name like "Dropcontact", "NeverBounce", etc.
        """
        pass
