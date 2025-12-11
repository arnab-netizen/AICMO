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
        Verify a single email address using Dropcontact API.
        
        Args:
            email: Email address to verify
            
        Returns:
            True if email is valid/deliverable, False otherwise
        """
        if not self.is_configured():
            logger.debug(f"Dropcontact not configured, optimistically approving {email}")
            return True
        
        if not email or "@" not in email:
            logger.debug(f"Invalid email format: {email}")
            return False
        
        try:
            import requests
            
            # Dropcontact email verification endpoint
            url = f"{self.api_base}/contact/verify"
            
            headers = {
                "X-Dropcontact-ApiKey": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "email": email,
                "phone": None,
                "name": None
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Dropcontact returns status codes:
            # "valid" / "valid_format_only" = good
            # "invalid" / "not_found" / "role" / "disposable" = bad
            # "unknown" = uncertain (we'll approve)
            
            status = data.get("status", "unknown")
            is_valid = status not in ["invalid", "not_found", "role", "disposable"]
            
            log_msg = f"Dropcontact verified {email}: {status}"
            if is_valid:
                logger.debug(log_msg)
            else:
                logger.info(log_msg)
            
            return is_valid
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Dropcontact API error for {email}: {e}")
            # Optimistic: approve on error (better to send and get bounce feedback)
            return True
        except Exception as e:
            logger.error(f"Dropcontact verification error for {email}: {e}")
            return True
    
    def verify_batch(self, emails: list[str]) -> Dict[str, bool]:
        """
        Verify multiple email addresses efficiently using Dropcontact batch API.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict mapping email -> validity
        """
        if not self.is_configured():
            logger.debug(f"Dropcontact not configured, optimistically approving {len(emails)} emails")
            return {email: True for email in emails}
        
        if not emails:
            return {}
        
        try:
            import requests
            
            # Dropcontact batch verification endpoint
            url = f"{self.api_base}/contact/verify/batch"
            
            headers = {
                "X-Dropcontact-ApiKey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Prepare batch payload (max 1000 per request)
            batch_size = 1000
            all_results = {}
            
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                
                payload = {
                    "contacts": [{"email": email} for email in batch]
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Process results
                if data.get("contacts"):
                    for contact in data["contacts"]:
                        email = contact.get("email")
                        status = contact.get("status", "unknown")
                        is_valid = status not in ["invalid", "not_found", "role", "disposable"]
                        all_results[email] = is_valid
            
            logger.info(f"Batch verified {len(all_results)} emails via Dropcontact")
            return all_results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Dropcontact batch verification API error: {e}")
            # Optimistic: approve all on error
            return {email: True for email in emails}
        except Exception as e:
            logger.error(f"Dropcontact batch verification error: {e}")
            return {email: True for email in emails}
    
    def is_configured(self) -> bool:
        """Check if Dropcontact API key is set."""
        return bool(self.api_key)
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "Dropcontact Verifier"
