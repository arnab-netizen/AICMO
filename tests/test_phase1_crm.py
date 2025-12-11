"""
Integration Tests for Phase 1: Mini-CRM and Enrichment Pipeline

Tests:
1. Contact Model Tests
2. CRM Repository Tests
3. Enrichment Pipeline Tests
4. Engagement Tracking Tests
5. Campaign Import Tests
6. Repository Persistence Tests

Run with: pytest tests/test_phase1_crm.py -v
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from aicmo.crm import (
    Contact,
    ContactStatus,
    EnrichmentData,
    EngagementType,
    CRMRepository,
    EnrichmentPipeline,
    get_crm_repository,
    reset_crm_repository,
    get_enrichment_pipeline,
    reset_enrichment_pipeline,
)


class TestContactModel:
    """Test Contact data model."""
    
    def test_contact_creation(self):
        """Test creating a contact."""
        contact = Contact(email="user@example.com", domain="example.com")
        assert contact.email == "user@example.com"
        assert contact.domain == "example.com"
        assert contact.status == ContactStatus.NEW
        assert contact.engagements == []
    
    def test_contact_with_details(self):
        """Test creating contact with full details."""
        contact = Contact(
            email="john@acme.com",
            domain="acme.com",
            first_name="John",
            last_name="Doe",
            company="Acme Inc",
            title="Manager"
        )
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.company == "Acme Inc"
        assert contact.title == "Manager"
    
    def test_contact_add_engagement(self):
        """Test adding engagement to contact."""
        contact = Contact(email="user@example.com", domain="example.com")
        assert len(contact.engagements) == 0
        assert contact.status == ContactStatus.NEW
        
        contact.add_engagement(EngagementType.EMAIL_SENT)
        assert len(contact.engagements) == 1
        assert contact.status == ContactStatus.ENGAGED
    
    def test_contact_add_multiple_engagements(self):
        """Test adding multiple engagements."""
        contact = Contact(email="user@example.com", domain="example.com")
        
        contact.add_engagement(EngagementType.EMAIL_SENT)
        contact.add_engagement(EngagementType.EMAIL_OPENED)
        contact.add_engagement(EngagementType.LINK_CLICKED)
        
        assert len(contact.engagements) == 3
        assert contact.status == ContactStatus.ENGAGED
    
    def test_contact_update_enrichment(self):
        """Test updating contact with enrichment data."""
        contact = Contact(email="user@example.com", domain="example.com")
        assert contact.enrichment is None
        assert contact.status == ContactStatus.NEW
        
        enrichment = EnrichmentData(
            company_name="Tech Corp",
            job_title="Engineer"
        )
        contact.update_enrichment(enrichment)
        
        assert contact.enrichment is not None
        assert contact.enrichment.company_name == "Tech Corp"
        assert contact.company == "Tech Corp"  # Auto-filled
        assert contact.status == ContactStatus.ENRICHED
    
    def test_contact_mark_verified(self):
        """Test marking email as verified."""
        enrichment = EnrichmentData(company_name="Acme")
        contact = Contact(email="user@example.com", domain="example.com")
        contact.update_enrichment(enrichment)
        
        assert contact.enrichment.email_verified == False
        contact.mark_verified()
        assert contact.enrichment.email_verified == True
        assert contact.enrichment.verification_timestamp is not None
    
    def test_contact_serialization(self):
        """Test converting contact to/from dict."""
        contact = Contact(
            email="user@example.com",
            domain="example.com",
            first_name="John",
            company="Acme"
        )
        contact.add_engagement(EngagementType.EMAIL_SENT)
        
        data = contact.to_dict()
        assert data["email"] == "user@example.com"
        assert data["first_name"] == "John"
        assert len(data["engagements"]) == 1
        
        # Deserialize
        contact2 = Contact.from_dict(data)
        assert contact2.email == contact.email
        assert contact2.first_name == contact.first_name
        assert len(contact2.engagements) == len(contact.engagements)
    
    def test_contact_tags(self):
        """Test contact tagging."""
        contact = Contact(email="user@example.com", domain="example.com")
        contact.tags.append("hot-lead")
        contact.tags.append("product-fit")
        
        assert "hot-lead" in contact.tags
        assert len(contact.tags) == 2


class TestEnrichmentData:
    """Test EnrichmentData model."""
    
    def test_enrichment_creation(self):
        """Test creating enrichment data."""
        enrichment = EnrichmentData(
            company_name="Acme Inc",
            job_title="VP Engineering",
            phone="+1-555-0100"
        )
        assert enrichment.company_name == "Acme Inc"
        assert enrichment.job_title == "VP Engineering"
        assert enrichment.email_verified == False
    
    def test_enrichment_serialization(self):
        """Test enrichment data serialization."""
        enrichment = EnrichmentData(
            company_name="Tech Corp",
            job_title="Manager",
            email_verified=True,
            enrichment_source="apollo"
        )
        
        data = enrichment.to_dict()
        assert data["company_name"] == "Tech Corp"
        assert data["email_verified"] == True
        
        enrichment2 = EnrichmentData.from_dict(data)
        assert enrichment2.company_name == enrichment.company_name
        assert enrichment2.email_verified == enrichment.email_verified


class TestCRMRepository:
    """Test CRM repository."""
    
    def setup_method(self):
        """Reset repository before each test."""
        reset_crm_repository()
        # Also clear the loaded data by creating fresh instance
        repo = get_crm_repository()
        repo.clear()
    
    def test_repository_singleton(self):
        """Test repository is singleton."""
        repo1 = get_crm_repository()
        repo2 = get_crm_repository()
        assert repo1 is repo2
    
    def test_add_and_retrieve_contact(self):
        """Test adding and retrieving contact."""
        repo = get_crm_repository()
        contact = Contact(email="user@example.com", domain="example.com")
        
        repo.add_contact(contact)
        retrieved = repo.get_contact("user@example.com")
        
        assert retrieved is not None
        assert retrieved.email == "user@example.com"
    
    def test_email_case_insensitive(self):
        """Test repository handles email case-insensitivity."""
        repo = get_crm_repository()
        contact = Contact(email="User@Example.com", domain="example.com")
        
        repo.add_contact(contact)
        retrieved = repo.get_contact("user@example.com")
        
        assert retrieved is not None
    
    def test_get_all_contacts(self):
        """Test retrieving all contacts."""
        repo = get_crm_repository()
        
        for i in range(5):
            contact = Contact(email=f"user{i}@example.com", domain="example.com")
            repo.add_contact(contact)
        
        all_contacts = repo.get_all_contacts()
        assert len(all_contacts) == 5
    
    def test_get_contacts_by_status(self):
        """Test filtering contacts by status."""
        repo = get_crm_repository()
        
        # Add NEW contact
        contact1 = Contact(email="new@example.com", domain="example.com")
        repo.add_contact(contact1)
        
        # Add ENRICHED contact
        contact2 = Contact(email="enriched@example.com", domain="example.com")
        contact2.status = ContactStatus.ENRICHED
        repo.add_contact(contact2)
        
        new_contacts = repo.get_contacts_by_status(ContactStatus.NEW)
        enriched_contacts = repo.get_contacts_by_status(ContactStatus.ENRICHED)
        
        assert len(new_contacts) == 1
        assert len(enriched_contacts) == 1
    
    def test_get_contacts_by_domain(self):
        """Test filtering contacts by domain."""
        repo = get_crm_repository()
        
        repo.add_contact(Contact(email="user1@example.com", domain="example.com"))
        repo.add_contact(Contact(email="user2@example.com", domain="example.com"))
        repo.add_contact(Contact(email="user3@acme.com", domain="acme.com"))
        
        example_contacts = repo.get_contacts_by_domain("example.com")
        acme_contacts = repo.get_contacts_by_domain("acme.com")
        
        assert len(example_contacts) == 2
        assert len(acme_contacts) == 1
    
    def test_get_contacts_by_tag(self):
        """Test filtering contacts by tag."""
        repo = get_crm_repository()
        
        contact1 = Contact(email="user1@example.com", domain="example.com")
        contact1.tags = ["hot-lead", "product-fit"]
        repo.add_contact(contact1)
        
        contact2 = Contact(email="user2@example.com", domain="example.com")
        contact2.tags = ["product-fit"]
        repo.add_contact(contact2)
        
        hot_leads = repo.get_contacts_by_tag("hot-lead")
        product_fit = repo.get_contacts_by_tag("product-fit")
        
        assert len(hot_leads) == 1
        assert len(product_fit) == 2
    
    def test_delete_contact(self):
        """Test deleting contact."""
        repo = get_crm_repository()
        contact = Contact(email="user@example.com", domain="example.com")
        repo.add_contact(contact)
        
        assert repo.get_contact("user@example.com") is not None
        
        deleted = repo.delete_contact("user@example.com")
        assert deleted == True
        assert repo.get_contact("user@example.com") is None
    
    def test_delete_nonexistent_contact(self):
        """Test deleting nonexistent contact."""
        repo = get_crm_repository()
        deleted = repo.delete_contact("nonexistent@example.com")
        assert deleted == False
    
    def test_get_statistics(self):
        """Test repository statistics."""
        repo = get_crm_repository()
        
        # Add contacts with different statuses
        for i in range(3):
            contact = Contact(email=f"new{i}@example.com", domain="example.com")
            repo.add_contact(contact)
        
        for i in range(2):
            contact = Contact(email=f"enriched{i}@example.com", domain="example.com")
            contact.status = ContactStatus.ENRICHED
            repo.add_contact(contact)
        
        stats = repo.get_statistics()
        
        assert stats["total_contacts"] == 5
        assert stats["by_status"]["new"] == 3
        assert stats["by_status"]["enriched"] == 2
    
    def test_contact_update(self):
        """Test updating existing contact."""
        repo = get_crm_repository()
        contact = Contact(email="user@example.com", domain="example.com")
        repo.add_contact(contact)
        
        # Update contact
        contact.first_name = "John"
        repo.add_contact(contact)
        
        retrieved = repo.get_contact("user@example.com")
        assert retrieved.first_name == "John"


class TestEnrichmentPipeline:
    """Test enrichment pipeline."""
    
    def setup_method(self):
        """Reset pipeline and repository before each test."""
        reset_enrichment_pipeline()
        reset_crm_repository()
        # Also clear the loaded data by creating fresh instance
        repo = get_crm_repository()
        repo.clear()
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes correctly."""
        pipeline = get_enrichment_pipeline()
        assert pipeline is not None
        assert pipeline.enricher is not None
        assert pipeline.verifier is not None
        assert pipeline.repository is not None
    
    @pytest.mark.asyncio
    async def test_enrich_single_contact(self):
        """Test enriching single contact."""
        contact = Contact(email="test@example.com", domain="example.com")
        pipeline = get_enrichment_pipeline()
        
        # This will use no-op providers if not configured
        enriched = await pipeline.enrich_contact(contact)
        assert enriched.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_enrich_batch(self):
        """Test enriching multiple contacts in parallel."""
        contacts = [
            Contact(email=f"user{i}@example.com", domain="example.com")
            for i in range(5)
        ]
        
        pipeline = get_enrichment_pipeline()
        enriched_contacts = await pipeline.enrich_batch(contacts)
        
        assert len(enriched_contacts) == 5
        assert all(c.email for c in enriched_contacts)
    
    def test_enrichment_statistics(self):
        """Test enrichment statistics."""
        repo = get_crm_repository()
        
        # Add some contacts
        for i in range(10):
            contact = Contact(email=f"user{i}@example.com", domain="example.com")
            if i < 5:
                enrichment = EnrichmentData(company_name="Acme")
                contact.update_enrichment(enrichment)
            repo.add_contact(contact)
        
        pipeline = get_enrichment_pipeline()
        stats = pipeline.get_enrichment_statistics()
        
        assert stats["total_contacts"] == 10
        assert stats["enriched_contacts"] == 5


class TestEngagementTracking:
    """Test engagement tracking."""
    
    def test_engagement_creation(self):
        """Test creating engagement."""
        contact = Contact(email="user@example.com", domain="example.com")
        contact.add_engagement(EngagementType.EMAIL_SENT)
        
        assert len(contact.engagements) == 1
        engagement = contact.engagements[0]
        assert engagement.engagement_type == EngagementType.EMAIL_SENT
    
    def test_engagement_with_metadata(self):
        """Test engagement with metadata."""
        contact = Contact(email="user@example.com", domain="example.com")
        metadata = {"campaign": "Q1 Launch", "content_id": "12345"}
        contact.add_engagement(EngagementType.EMAIL_OPENED, metadata)
        
        assert contact.engagements[0].metadata == metadata
    
    def test_engagement_updates_status(self):
        """Test engagement updates contact status."""
        contact = Contact(email="user@example.com", domain="example.com")
        assert contact.status == ContactStatus.NEW
        
        contact.add_engagement(EngagementType.LINK_CLICKED)
        assert contact.status == ContactStatus.ENGAGED


class TestRepositoryPersistence:
    """Test repository file persistence."""
    
    def setup_method(self):
        """Reset before each test."""
        reset_crm_repository()
    
    def test_persistence_to_file(self, tmp_path):
        """Test contacts are persisted to file."""
        storage_file = tmp_path / "contacts.json"
        repo = CRMRepository(storage_path=storage_file)
        
        contact = Contact(email="user@example.com", domain="example.com")
        contact.first_name = "John"
        repo.add_contact(contact)
        
        # File should exist
        assert storage_file.exists()
        
        # Load file and verify content
        import json
        with open(storage_file, 'r') as f:
            data = json.load(f)
            assert "user@example.com" in data
            assert data["user@example.com"]["first_name"] == "John"
    
    def test_load_from_persistent_file(self, tmp_path):
        """Test loading contacts from persistent file."""
        storage_file = tmp_path / "contacts.json"
        
        # Create repo and add contact
        repo1 = CRMRepository(storage_path=storage_file)
        contact = Contact(email="user@example.com", domain="example.com")
        contact.first_name = "John"
        repo1.add_contact(contact)
        
        # Create new repo with same file
        repo2 = CRMRepository(storage_path=storage_file)
        
        # Should load existing contact
        loaded = repo2.get_contact("user@example.com")
        assert loaded is not None
        assert loaded.first_name == "John"


# Pytest async support
pytest_plugins = ('pytest_asyncio',)
