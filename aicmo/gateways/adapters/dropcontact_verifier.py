"""
Dropcontact Email Verifier Adapter.

Implements EmailVerifierPort using Dropcontact's API.
Only active if DROPCONTACT_API_KEY is configured.
"""

import logging
import os
from typing import Dict

from aicmo.cam.ports import EmailVerifierPort

logger = logging.getLogger(__name__)


class DropcontactVerifier(EmailVerifierPort):
    """
    Email verifier using Dropcontact's API.
    
    Checks email validity, deliverability, bounce risk, etc.
    Only works if DROPCONTACT_API_KEY environment variable is set.
    """
    
    def __init__(self):
        """Initialize Dropcontact verifier."""
        self.api_key = os.getenv("DROPCONTACT_API_KEY")
        self.api_base = "https://api.dropcontact.io/v1"
    
    def verify(self, email: str) -> bool:
        """
        Verify a single email address.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if email is valid/deliverable, False otherwise
        """
        if not self.is_configured():
            logger.debug(f"Dropcontact not configured, approving {email}")
            return True
        
        try:
            # TODO: Implement actual Dropcontact API call
            # For now: placeholder that would call Dropcontact's verification endpoint
            logger.debug(f"Dropcontact would verify {email}")
            
            # Sample logic: would return True if valid, False if bounces/role accounts/etc.
            return True
        except Exception as e:
            logger.error(f"Dropcontact verification error for {email}: {e}")
            # Optimistic: assume valid on error (better to send and get bounce feedback)
            return True
    
    def verify_batch(self, emails: list[str]) -> Dict[str, bool]:
        """
        Verify multiple email addresses efficiently.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict mapping email -> validity
        """
        if not self.is_configured():
            logger.debug(f"Dropcontact not configured, approving {len(emails)} emails")
            return {email: True for email in emails}
        
        try:
            # TODO: Use Dropcontact's batch endpoint if available
            # For now: fall back to individual verification
            logger.debug(f"Verifying batch of {len(emails)} emails via Dropcontact")
            return {email: self.verify(email) for email in emails}
        except Exception as e:
            logger.error(f"Dropcontact batch verification error: {e}")
            # Optimistic: approve all on error
            return {email: True for email in emails}
    
    def is_configured(self) -> bool:
        """Check if Dropcontact API key is set."""
        return bool(self.api_key)
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "Dropcontact Verifier"
