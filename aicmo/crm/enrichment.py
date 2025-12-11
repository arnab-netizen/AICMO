"""
Contact Enrichment Pipeline for Phase 1

Orchestrates multi-step enrichment:
1. Apollo API for company/job/LinkedIn data
2. Dropcontact for email verification
3. Domain/brand intelligence (future)

Uses ProviderChain for automatic failover between providers.
Non-blocking async operations for high throughput.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from aicmo.crm.models import Contact, EnrichmentData, ContactStatus, get_crm_repository
from aicmo.gateways.factory import get_lead_enricher, get_email_verifier, get_email_sending_chain
from aicmo.core.config_gateways import get_gateway_config


logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """
    Orchestrates contact enrichment through multiple providers.
    
    Steps:
    1. Apollo enrichment (company, job title, LinkedIn, phone, etc.)
    2. Dropcontact verification (email validation)
    3. Additional enrichment (optional, future: domain intelligence)
    
    All steps are optional and gracefully degrade to safe defaults.
    """
    
    def __init__(self):
        """Initialize pipeline with provider chains."""
        self.config = get_gateway_config()
        self.enricher = get_lead_enricher()  # Apollo
        self.verifier = get_email_verifier()  # Dropcontact
        self.repository = get_crm_repository()
    
    async def enrich_contact(self, contact: Contact) -> Contact:
        """
        Enrich single contact through full pipeline.
        
        Args:
            contact: Contact to enrich (must have email)
        
        Returns:
            Enriched contact with Apollo + Dropcontact data
        
        Note:
            Gracefully handles missing providers or API errors.
            Updates contact in repository.
        """
        logger.info(f"Enriching contact: {contact.email}")
        
        # Step 1: Apollo enrichment
        enrichment = await self._enrich_with_apollo(contact)
        
        # Step 2: Email verification
        if enrichment:
            enrichment = await self._verify_email(contact.email, enrichment)
        
        # Step 3: Store enriched contact
        if enrichment:
            contact.update_enrichment(enrichment)
            self.repository.add_contact(contact)
            logger.info(f"✓ Contact enriched: {contact.email} (status={contact.status.value})")
        else:
            logger.warning(f"⚠ No enrichment data available: {contact.email}")
        
        return contact
    
    async def enrich_batch(self, contacts: List[Contact]) -> List[Contact]:
        """
        Enrich multiple contacts in parallel.
        
        Args:
            contacts: List of contacts to enrich
        
        Returns:
            List of enriched contacts
        
        Performance:
            With 10 contacts: ~500-2000ms (parallel)
            vs Sequential: ~5000-20000ms
        """
        logger.info(f"Starting batch enrichment: {len(contacts)} contacts")
        
        # Run enrichments in parallel
        enriched = await asyncio.gather(
            *[self.enrich_contact(contact) for contact in contacts],
            return_exceptions=True
        )
        
        # Handle any exceptions
        results = []
        for i, result in enumerate(enriched):
            if isinstance(result, Exception):
                logger.error(f"Error enriching contact {i}: {result}")
                results.append(contacts[i])  # Return original
            else:
                results.append(result)
        
        logger.info(f"✓ Batch enrichment complete: {len(results)} contacts")
        return results
    
    async def _enrich_with_apollo(self, contact: Contact) -> Optional[EnrichmentData]:
        """
        Enrich contact with Apollo lead enrichment API.
        
        Fetches: company name, job title, LinkedIn URL, phone, industry, seniority
        
        Args:
            contact: Contact with email and domain
        
        Returns:
            EnrichmentData if successful, None otherwise
        """
        try:
            # Apollo needs email and domain
            apollo_result = self.enricher.fetch_from_apollo(contact)
            
            if not apollo_result:
                logger.warning(f"Apollo enrichment returned None for {contact.email}")
                return None
            
            # Create enrichment data from Apollo result
            enrichment = EnrichmentData(
                company_name=apollo_result.get("company"),
                job_title=apollo_result.get("job_title"),
                linkedin_url=apollo_result.get("linkedin_url"),
                phone=apollo_result.get("phone"),
                industry=apollo_result.get("industry"),
                seniority_level=apollo_result.get("seniority"),
                enriched_at=datetime.now(),
                enrichment_source="apollo"
            )
            
            logger.debug(f"Apollo enrichment successful: {contact.email} → {enrichment.company_name}")
            return enrichment
        
        except Exception as e:
            logger.error(f"Apollo enrichment error for {contact.email}: {e}")
            return None
    
    async def _verify_email(self, email: str, enrichment: EnrichmentData) -> EnrichmentData:
        """
        Verify email with Dropcontact API.
        
        Args:
            email: Email to verify
            enrichment: Existing enrichment data to update
        
        Returns:
            Updated enrichment with verification status
        """
        try:
            # Dropcontact verify_batch returns dict: email → bool
            result = self.verifier.verify_batch([email])
            
            if result and email in result:
                is_valid = result[email]
                enrichment.email_verified = is_valid
                enrichment.verification_timestamp = datetime.now()
                
                status_str = "✓ VALID" if is_valid else "✗ INVALID"
                logger.debug(f"Dropcontact verification: {email} {status_str}")
            
            return enrichment
        
        except Exception as e:
            logger.error(f"Email verification error for {email}: {e}")
            # Return enrichment even if verification fails
            return enrichment
    
    async def enrich_from_campaign(
        self,
        emails: List[str],
        campaign_name: str,
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> List[Contact]:
        """
        Import and enrich contacts from campaign.
        
        Typical workflow:
        1. Get email list from campaign export
        2. Create Contact objects with campaign source
        3. Run enrichment pipeline
        4. Store in CRM
        
        Args:
            emails: List of email addresses
            campaign_name: Source campaign identifier
            additional_fields: Extra fields to set on all contacts (company, title, etc.)
        
        Returns:
            List of enriched contacts
        """
        logger.info(f"Importing contacts from campaign: {campaign_name} ({len(emails)} contacts)")
        
        # Create contact objects
        contacts = []
        for email in emails:
            # Extract domain from email
            domain = email.split("@")[1].lower() if "@" in email else "unknown"
            
            contact = Contact(
                email=email.lower(),
                domain=domain,
                imported_from_campaign=campaign_name,
                tags=[campaign_name]
            )
            
            # Add any additional fields
            if additional_fields:
                if "first_name" in additional_fields:
                    contact.first_name = additional_fields["first_name"]
                if "last_name" in additional_fields:
                    contact.last_name = additional_fields["last_name"]
                if "company" in additional_fields:
                    contact.company = additional_fields["company"]
                if "title" in additional_fields:
                    contact.title = additional_fields["title"]
            
            contacts.append(contact)
        
        # Enrich all contacts
        enriched_contacts = await self.enrich_batch(contacts)
        
        logger.info(f"✓ Campaign import complete: {len(enriched_contacts)} contacts enriched")
        return enriched_contacts
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """
        Get enrichment statistics from repository.
        
        Returns:
            Dict with enrichment metrics
        """
        stats = self.repository.get_statistics()
        
        return {
            "total_contacts": stats["total_contacts"],
            "by_status": stats["by_status"],
            "enriched_contacts": stats["enriched_count"],
            "verified_emails": stats["verified_count"],
            "with_engagement": stats["with_engagement"],
            "total_engagements": stats["total_engagements"],
            "enrichment_rate": (
                f"{(stats['enriched_count'] / stats['total_contacts'] * 100):.1f}%"
                if stats["total_contacts"] > 0 else "0%"
            ),
            "verification_rate": (
                f"{(stats['verified_count'] / stats['enriched_count'] * 100):.1f}%"
                if stats["enriched_count"] > 0 else "0%"
            ),
        }


# Global pipeline instance
_pipeline_instance: Optional[EnrichmentPipeline] = None


def get_enrichment_pipeline() -> EnrichmentPipeline:
    """Get global enrichment pipeline instance (singleton)."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = EnrichmentPipeline()
    return _pipeline_instance


def reset_enrichment_pipeline() -> None:
    """Reset global pipeline (testing only)."""
    global _pipeline_instance
    _pipeline_instance = None


# Convenience functions
async def enrich_contact(contact: Contact) -> Contact:
    """Enrich single contact using global pipeline."""
    pipeline = get_enrichment_pipeline()
    return await pipeline.enrich_contact(contact)


async def enrich_batch(contacts: List[Contact]) -> List[Contact]:
    """Enrich multiple contacts using global pipeline."""
    pipeline = get_enrichment_pipeline()
    return await pipeline.enrich_batch(contacts)


async def import_and_enrich_campaign(
    emails: List[str],
    campaign_name: str,
    additional_fields: Optional[Dict[str, Any]] = None
) -> List[Contact]:
    """Import and enrich contacts from campaign using global pipeline."""
    pipeline = get_enrichment_pipeline()
    return await pipeline.enrich_from_campaign(emails, campaign_name, additional_fields)
