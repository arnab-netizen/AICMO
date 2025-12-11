"""
Mini-CRM Data Models for Phase 1

Manages contacts, enrichment data, and engagement tracking without external database.
Uses in-memory storage with file-based persistence for development/testing.

Classes:
- ContactStatus: Enum for contact states (new, enriched, engaged, converted, disqualified)
- EnrichmentData: Rich contact information (Apollo enrichment + Dropcontact verification)
- Contact: Core contact model with audit trail
- CRMRepository: In-memory storage with persistence
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import threading


class ContactStatus(Enum):
    """Contact lifecycle states."""
    NEW = "new"  # Just added to CRM
    ENRICHED = "enriched"  # Has enrichment data
    VERIFIED = "verified"  # Email verified
    ENGAGED = "engaged"  # Has engagement activity
    CONVERTED = "converted"  # Sales cycle completed
    DISQUALIFIED = "disqualified"  # Not qualified


class EngagementType(Enum):
    """Types of contact engagement."""
    EMAIL_SENT = "email_sent"
    EMAIL_OPENED = "email_opened"
    LINK_CLICKED = "link_clicked"
    REPLY_RECEIVED = "reply_received"
    WEBSITE_VISIT = "website_visit"
    FORM_SUBMISSION = "form_submission"
    CALL_SCHEDULED = "call_scheduled"
    CALL_COMPLETED = "call_completed"
    DEMO_ATTENDED = "demo_attended"


@dataclass
class EnrichmentData:
    """Contact enrichment from Apollo and verification from Dropcontact."""
    
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    seniority_level: Optional[str] = None
    company_size: Optional[str] = None
    
    # From Dropcontact verification
    email_verified: bool = False
    verification_timestamp: Optional[datetime] = None
    
    # Metadata
    enriched_at: Optional[datetime] = None
    enrichment_source: Optional[str] = None  # "apollo", "dropcontact", etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "company_name": self.company_name,
            "job_title": self.job_title,
            "linkedin_url": self.linkedin_url,
            "phone": self.phone,
            "industry": self.industry,
            "seniority_level": self.seniority_level,
            "company_size": self.company_size,
            "email_verified": self.email_verified,
            "verification_timestamp": self.verification_timestamp.isoformat() if self.verification_timestamp else None,
            "enriched_at": self.enriched_at.isoformat() if self.enriched_at else None,
            "enrichment_source": self.enrichment_source,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EnrichmentData":
        """Create from dictionary."""
        return EnrichmentData(
            company_name=data.get("company_name"),
            job_title=data.get("job_title"),
            linkedin_url=data.get("linkedin_url"),
            phone=data.get("phone"),
            industry=data.get("industry"),
            seniority_level=data.get("seniority_level"),
            company_size=data.get("company_size"),
            email_verified=data.get("email_verified", False),
            verification_timestamp=datetime.fromisoformat(data["verification_timestamp"]) if data.get("verification_timestamp") else None,
            enriched_at=datetime.fromisoformat(data["enriched_at"]) if data.get("enriched_at") else None,
            enrichment_source=data.get("enrichment_source"),
        )


@dataclass
class Engagement:
    """Single engagement event."""
    engagement_type: EngagementType
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "engagement_type": self.engagement_type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Engagement":
        """Create from dictionary."""
        return Engagement(
            engagement_type=EngagementType(data["engagement_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Contact:
    """Core contact model with audit trail."""
    
    email: str
    domain: str  # Extracted from email for filtering
    status: ContactStatus = ContactStatus.NEW
    
    # Contact info
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    
    # Enrichment data (from Apollo + Dropcontact)
    enrichment: Optional[EnrichmentData] = None
    
    # Engagement history
    engagements: List[Engagement] = field(default_factory=list)
    
    # Audit fields
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    imported_from_campaign: Optional[str] = None  # Campaign source
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def add_engagement(self, engagement_type: EngagementType, metadata: Dict[str, Any] = None) -> None:
        """Record engagement event."""
        engagement = Engagement(
            engagement_type=engagement_type,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.engagements.append(engagement)
        self.updated_at = datetime.now()
        
        # Auto-update status to engaged if not already
        if self.status not in (ContactStatus.ENGAGED, ContactStatus.CONVERTED, ContactStatus.DISQUALIFIED):
            self.status = ContactStatus.ENGAGED
    
    def update_enrichment(self, enrichment: EnrichmentData) -> None:
        """Update enrichment data."""
        self.enrichment = enrichment
        self.updated_at = datetime.now()
        
        # Auto-update status if enrichment received
        if self.status == ContactStatus.NEW:
            self.status = ContactStatus.ENRICHED
        
        # Update contact fields from enrichment if not set
        if not self.company and enrichment.company_name:
            self.company = enrichment.company_name
        if not self.title and enrichment.job_title:
            self.title = enrichment.job_title
    
    def mark_verified(self) -> None:
        """Mark email as verified."""
        if self.enrichment:
            self.enrichment.email_verified = True
            self.enrichment.verification_timestamp = datetime.now()
        self.updated_at = datetime.now()
        
        if self.status == ContactStatus.ENRICHED:
            self.status = ContactStatus.VERIFIED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "email": self.email,
            "domain": self.domain,
            "status": self.status.value,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "title": self.title,
            "enrichment": self.enrichment.to_dict() if self.enrichment else None,
            "engagements": [e.to_dict() for e in self.engagements],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "imported_from_campaign": self.imported_from_campaign,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Contact":
        """Create from dictionary."""
        return Contact(
            email=data["email"],
            domain=data["domain"],
            status=ContactStatus(data.get("status", "new")),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            company=data.get("company"),
            title=data.get("title"),
            enrichment=EnrichmentData.from_dict(data["enrichment"]) if data.get("enrichment") else None,
            engagements=[Engagement.from_dict(e) for e in data.get("engagements", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            imported_from_campaign=data.get("imported_from_campaign"),
            tags=data.get("tags", []),
            custom_fields=data.get("custom_fields", {}),
        )


class CRMRepository:
    """
    In-memory contact repository with file-based persistence.
    
    Thread-safe storage for contacts with enrichment data and engagement history.
    Designed for development/testing. Production deployments would use PostgreSQL.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize repository.
        
        Args:
            storage_path: Optional path to persist contacts to JSON file.
                         If None, uses {project_root}/data/contacts.json
        """
        self._contacts: Dict[str, Contact] = {}
        self._lock = threading.RLock()
        
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "data" / "contacts.json"
        
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing contacts
        self._load_from_file()
    
    def add_contact(self, contact: Contact) -> None:
        """Add or update contact."""
        with self._lock:
            self._contacts[contact.email.lower()] = contact
            self._persist_to_file()
    
    def get_contact(self, email: str) -> Optional[Contact]:
        """Retrieve contact by email."""
        with self._lock:
            return self._contacts.get(email.lower())
    
    def get_contacts_by_status(self, status: ContactStatus) -> List[Contact]:
        """Retrieve all contacts with given status."""
        with self._lock:
            return [c for c in self._contacts.values() if c.status == status]
    
    def get_contacts_by_domain(self, domain: str) -> List[Contact]:
        """Retrieve all contacts from a domain."""
        with self._lock:
            return [c for c in self._contacts.values() if c.domain.lower() == domain.lower()]
    
    def get_contacts_by_tag(self, tag: str) -> List[Contact]:
        """Retrieve all contacts with given tag."""
        with self._lock:
            return [c for c in self._contacts.values() if tag in c.tags]
    
    def get_all_contacts(self) -> List[Contact]:
        """Retrieve all contacts."""
        with self._lock:
            return list(self._contacts.values())
    
    def delete_contact(self, email: str) -> bool:
        """Delete contact by email. Returns True if deleted, False if not found."""
        with self._lock:
            if email.lower() in self._contacts:
                del self._contacts[email.lower()]
                self._persist_to_file()
                return True
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        with self._lock:
            contacts = list(self._contacts.values())
            
            return {
                "total_contacts": len(contacts),
                "by_status": {
                    status.value: len([c for c in contacts if c.status == status])
                    for status in ContactStatus
                },
                "enriched_count": len([c for c in contacts if c.enrichment]),
                "verified_count": len([c for c in contacts if c.enrichment and c.enrichment.email_verified]),
                "with_engagement": len([c for c in contacts if c.engagements]),
                "total_engagements": sum(len(c.engagements) for c in contacts),
            }
    
    def clear(self) -> None:
        """Clear all contacts (testing only)."""
        with self._lock:
            self._contacts.clear()
            if self.storage_path.exists():
                self.storage_path.unlink()
    
    def _persist_to_file(self) -> None:
        """Save contacts to JSON file."""
        try:
            data = {
                email: contact.to_dict()
                for email, contact in self._contacts.items()
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Log error but don't crash - in-memory store still works
            print(f"Warning: Failed to persist contacts: {e}")
    
    def _load_from_file(self) -> None:
        """Load contacts from JSON file."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self._contacts = {
                        email: Contact.from_dict(contact_data)
                        for email, contact_data in data.items()
                    }
        except Exception as e:
            # Start with empty repository if file can't be loaded
            print(f"Warning: Failed to load contacts from file: {e}")
            self._contacts = {}


# Global repository instance
_repository_instance: Optional[CRMRepository] = None
_repository_lock = threading.Lock()


def get_crm_repository(storage_path: Optional[Path] = None) -> CRMRepository:
    """Get global CRM repository instance (singleton pattern)."""
    global _repository_instance
    
    if _repository_instance is None:
        with _repository_lock:
            if _repository_instance is None:
                _repository_instance = CRMRepository(storage_path)
    
    return _repository_instance


def reset_crm_repository() -> None:
    """Reset global repository (testing only)."""
    global _repository_instance
    _repository_instance = None
