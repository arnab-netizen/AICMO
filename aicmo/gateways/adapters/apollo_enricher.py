"""
Apollo Lead Enricher Adapter.

Implements LeadEnricherPort using Apollo's API.
Only active if APOLLO_API_KEY is configured.
"""

import logging
import os
from typing import List, Dict, Optional, Any

from aicmo.cam.ports import LeadEnricherPort
from aicmo.cam.domain import Lead

logger = logging.getLogger(__name__)


class ApolloEnricher(LeadEnricherPort):
    """
    Lead enricher using Apollo's API.
    
    Enriches leads with company info, job titles, email, LinkedIn profile, etc.
    Only works if APOLLO_API_KEY environment variable is set.
    """
    
    def __init__(self):
        """Initialize Apollo enricher."""
        self.api_key = os.getenv("APOLLO_API_KEY")
        self.api_base = "https://api.apollo.io/v1"
    
    def fetch_from_apollo(self, lead: Lead) -> Optional[Dict[str, Any]]:
        """
        Fetch enrichment data from Apollo for a single lead.
        
        Args:
            lead: Lead to enrich
            
        Returns:
            Dict with enrichment data, or None if not found/error
        """
        if not self.is_configured():
            return None
        
        if not lead.email:
            return None
        
        try:
            import requests
            from datetime import datetime
            
            # Apollo People Search endpoint
            url = f"{self.api_base}/people/search"
            
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q_emails": [lead.email],
                "reveal_personal_emails": True
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("contacts") and len(data["contacts"]) > 0:
                contact = data["contacts"][0]
                
                enrichment = {
                    "source": "apollo",
                    "enriched_at": datetime.utcnow().isoformat(),
                    "contact_id": contact.get("id"),
                    "email_status": contact.get("email_status"),  # verified, bounced, etc.
                    "company": contact.get("organization", {}).get("name"),
                    "job_title": contact.get("title"),
                    "linkedin_url": contact.get("linkedin_url"),
                    "phone": contact.get("phone_number"),
                    "industry": contact.get("organization", {}).get("industry"),
                    "company_size": contact.get("organization", {}).get("size"),
                    "seniority_level": contact.get("seniority"),
                }
                
                logger.info(f"Apollo enriched {lead.email}: {contact.get('title')} at {contact.get('organization', {}).get('name')}")
                return enrichment
            else:
                logger.debug(f"Apollo: No data found for {lead.email}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API request error for {lead.email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Apollo enrichment error for {lead.email}: {e}")
            return None
    
    def enrich(self, lead: Lead) -> Lead:
        """
        Enrich a single lead with Apollo data.
        
        Args:
            lead: Lead to enrich
            
        Returns:
            Lead with enrichment_data populated
        """
        if not lead.email:
            logger.debug(f"Cannot enrich lead {lead.name}: no email")
            return lead
        
        enrichment = self.fetch_from_apollo(lead)
        if enrichment:
            lead.enrichment_data = lead.enrichment_data or {}
            lead.enrichment_data.update(enrichment)
            logger.info(f"Enriched lead {lead.name} via Apollo")
        
        return lead
    
    def enrich_batch(self, leads: list[Lead]) -> list[Lead]:
        """
        Enrich multiple leads in batch (more efficient than individual calls).
        
        Args:
            leads: List of leads to enrich
            
        Returns:
            List of enriched leads
        """
        if not self.is_configured():
            logger.debug(f"Apollo not configured, returning {len(leads)} leads unenriched")
            return leads
        
        if not leads:
            return leads
        
        try:
            import requests
            from datetime import datetime
            
            # Filter leads with emails
            enrichable_leads = [lead for lead in leads if lead.email]
            if not enrichable_leads:
                return leads
            
            # Apollo People Search with batch of emails
            url = f"{self.api_base}/people/search"
            
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q_emails": [lead.email for lead in enrichable_leads],
                "reveal_personal_emails": True
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Build email -> contact data mapping
            contact_map = {}
            if data.get("contacts"):
                for contact in data["contacts"]:
                    email = contact.get("email")
                    if email:
                        contact_map[email] = contact
            
            # Update leads with enrichment data
            enriched_count = 0
            for lead in enrichable_leads:
                if lead.email in contact_map:
                    contact = contact_map[lead.email]
                    lead.enrichment_data = lead.enrichment_data or {}
                    lead.enrichment_data.update({
                        "source": "apollo",
                        "enriched_at": datetime.utcnow().isoformat(),
                        "contact_id": contact.get("id"),
                        "email_status": contact.get("email_status"),
                        "company": contact.get("organization", {}).get("name"),
                        "job_title": contact.get("title"),
                        "linkedin_url": contact.get("linkedin_url"),
                        "phone": contact.get("phone_number"),
                        "industry": contact.get("organization", {}).get("industry"),
                        "company_size": contact.get("organization", {}).get("size"),
                        "seniority_level": contact.get("seniority"),
                    })
                    enriched_count += 1
            
            logger.info(f"Enriched {enriched_count}/{len(enrichable_leads)} leads via Apollo")
            return leads
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo batch enrichment API error: {e}")
            return leads
        except Exception as e:
            logger.error(f"Apollo batch enrichment error: {e}")
            return leads
    
    def is_configured(self) -> bool:
        """Check if Apollo API key is set."""
        return bool(self.api_key)
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "Apollo Enricher"
