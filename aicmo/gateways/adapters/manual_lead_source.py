"""
Manual Lead Source Adapter.

Implements LeadSourcePort to add leads via manual entry (API, UI, etc).
Stores leads in a simple in-memory queue or database staging table.

Use case:
- Users upload leads via UI form
- Leads are added to a staging queue
- Harvest pipeline picks them up and processes

This adapter provides:
- add_lead() / add_leads() methods to add leads to queue
- fetch_new_leads() to retrieve queued leads
- mark_as_processed() to track which leads have been processed
"""

import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from aicmo.cam.ports.lead_source import LeadSourcePort
from aicmo.cam.domain import Lead, Campaign, LeadSource

logger = logging.getLogger(__name__)


@dataclass
class PendingLead:
    """Lead pending processing from manual source."""
    
    lead: Lead
    added_at: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    processed_at: Optional[datetime] = None


class ManualLeadSource(LeadSourcePort):
    """
    Manual lead source adapter.
    
    Allows leads to be added programmatically (e.g., via API endpoint).
    Maintains a queue of pending leads until they're harvested.
    
    Can be connected to:
    - API endpoint for UI form submissions
    - Email-based lead capture
    - Webhook from third-party tools
    """
    
    # Class-level storage (in-memory queue)
    # In production, would use a database table instead
    _pending_leads: Dict[int, PendingLead] = {}
    _next_id: int = 1
    
    def __init__(self):
        """Initialize manual lead source."""
        self.name = "Manual Lead Source"
    
    def is_configured(self) -> bool:
        """
        Check if manual source is configured.
        
        Returns:
            Always True (manual source is always available)
        """
        return True
    
    def add_lead(
        self,
        name: str,
        email: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        enrichment_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> int:
        """
        Add a single lead to the queue.
        
        Args:
            name: Contact name (required)
            email: Email address (required)
            company: Company name (optional)
            role: Job title (optional)
            linkedin_url: LinkedIn profile URL (optional)
            enrichment_data: Additional fields (optional)
            tags: Lead tags (optional)
            
        Returns:
            Lead ID in queue
            
        Raises:
            ValueError: If required fields missing or invalid
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("Lead name is required")
        
        if not email or "@" not in email:
            raise ValueError("Lead email is required and must be valid")
        
        # Create Lead object
        lead = Lead(
            name=name.strip(),
            email=email.strip().lower(),
            company=company.strip() if company else None,
            role=role.strip() if role else None,
            linkedin_url=linkedin_url.strip() if linkedin_url else None,
            source=LeadSource.MANUAL,
            lead_score=0.5,  # Default; will be scored in pipeline
            enrichment_data=enrichment_data or None,
            tags=tags or ["manual_entry"],
        )
        
        # Add to queue
        lead_id = self._next_id
        self._pending_leads[lead_id] = PendingLead(lead=lead)
        self._next_id += 1
        
        logger.info(f"Added manual lead #{lead_id}: {name} ({email})")
        return lead_id
    
    def add_leads(
        self,
        leads_data: List[Dict],
    ) -> List[int]:
        """
        Add multiple leads to the queue.
        
        Args:
            leads_data: List of lead dictionaries with fields:
                - name (required)
                - email (required)
                - company, role, linkedin_url, enrichment_data, tags (optional)
        
        Returns:
            List of lead IDs added to queue
            
        Raises:
            ValueError: If any lead is invalid
        """
        lead_ids = []
        
        for i, lead_data in enumerate(leads_data):
            try:
                lead_id = self.add_lead(
                    name=lead_data.get("name"),
                    email=lead_data.get("email"),
                    company=lead_data.get("company"),
                    role=lead_data.get("role"),
                    linkedin_url=lead_data.get("linkedin_url"),
                    enrichment_data=lead_data.get("enrichment_data"),
                    tags=lead_data.get("tags"),
                )
                lead_ids.append(lead_id)
            except ValueError as e:
                logger.error(f"Invalid lead at index {i}: {e}")
                raise
        
        logger.info(f"Added {len(lead_ids)} manual leads")
        return lead_ids
    
    def fetch_new_leads(
        self,
        campaign: Campaign,
        max_leads: int = 50,
    ) -> List[Lead]:
        """
        Fetch unprocessed leads from the queue.
        
        Args:
            campaign: Campaign to fetch leads for (used for logging)
            max_leads: Maximum number of leads to return
            
        Returns:
            List of unprocessed Lead objects
        """
        leads = []
        
        for lead_id, pending in list(self._pending_leads.items()):
            # Skip already-processed leads
            if pending.processed:
                continue
            
            leads.append(pending.lead)
            
            if len(leads) >= max_leads:
                break
        
        logger.info(
            f"Manual source returning {len(leads)} unprocessed leads "
            f"({len([p for p in self._pending_leads.values() if p.processed])} processed)"
        )
        
        return leads
    
    def mark_as_processed(self, lead_ids: List[int]) -> int:
        """
        Mark leads as processed (no longer returned by fetch_new_leads).
        
        Typically called after leads are harvested and stored in database.
        
        Args:
            lead_ids: List of lead IDs to mark as processed
            
        Returns:
            Number of leads marked as processed
        """
        count = 0
        now = datetime.utcnow()
        
        for lead_id in lead_ids:
            if lead_id in self._pending_leads:
                self._pending_leads[lead_id].processed = True
                self._pending_leads[lead_id].processed_at = now
                count += 1
        
        logger.info(f"Marked {count} leads as processed")
        return count
    
    def get_pending_count(self) -> int:
        """
        Get count of unprocessed leads.
        
        Returns:
            Number of leads in queue
        """
        return len([p for p in self._pending_leads.values() if not p.processed])
    
    def get_processed_count(self) -> int:
        """
        Get count of processed leads.
        
        Returns:
            Number of processed leads
        """
        return len([p for p in self._pending_leads.values() if p.processed])
    
    def clear_queue(self) -> None:
        """Clear all leads from queue (use with caution)."""
        self._pending_leads.clear()
        self._next_id = 1
        logger.warning("Manual lead queue cleared")
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Get queue statistics.
        
        Returns:
            Dict with pending/processed/total counts
        """
        pending = len([p for p in self._pending_leads.values() if not p.processed])
        processed = len([p for p in self._pending_leads.values() if p.processed])
        
        return {
            "pending": pending,
            "processed": processed,
            "total": pending + processed,
        }
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "Manual Lead Source"
    
    @classmethod
    def reset_queue(cls) -> None:
        """Reset the global queue (for testing)."""
        cls._pending_leads.clear()
        cls._next_id = 1
