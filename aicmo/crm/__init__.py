"""
AICMO Mini-CRM Module - Phase 1

Provides contact management, enrichment, and engagement tracking.

Key components:
- models: Contact, EnrichmentData, CRMRepository
- enrichment: Multi-provider enrichment pipeline
- repository: In-memory persistent storage

Usage:
    from aicmo.crm import get_crm_repository, enrich_contact
    from aicmo.crm.models import Contact
    
    # Create contact
    contact = Contact(email="user@example.com", domain="example.com")
    
    # Enrich with Apollo + Dropcontact
    enriched = await enrich_contact(contact)
    
    # Access repository
    repo = get_crm_repository()
    all_contacts = repo.get_all_contacts()
    stats = repo.get_statistics()
"""

from aicmo.crm.models import (
    Contact,
    ContactStatus,
    EnrichmentData,
    EngagementType,
    Engagement,
    CRMRepository,
    get_crm_repository,
    reset_crm_repository,
)

from aicmo.crm.enrichment import (
    EnrichmentPipeline,
    get_enrichment_pipeline,
    reset_enrichment_pipeline,
    enrich_contact,
    enrich_batch,
    import_and_enrich_campaign,
)

__all__ = [
    # Models
    "Contact",
    "ContactStatus",
    "EnrichmentData",
    "EngagementType",
    "Engagement",
    "CRMRepository",
    # Repository functions
    "get_crm_repository",
    "reset_crm_repository",
    # Pipeline
    "EnrichmentPipeline",
    "get_enrichment_pipeline",
    "reset_enrichment_pipeline",
    # Convenience functions
    "enrich_contact",
    "enrich_batch",
    "import_and_enrich_campaign",
]
