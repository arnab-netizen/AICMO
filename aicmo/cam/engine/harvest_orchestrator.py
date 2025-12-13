"""
Lead Harvest Orchestrator.

Coordinates multi-source lead harvesting with fallback chains and batch processing.

Phase 2 Implementation: Core harvesting engine for Lead Generation & Client Acquisition.

Key Features:
1. Multi-source provider chains with fallback logic
2. Automatic deduplication across sources
3. Rate limiting and error handling
4. Batch processing and insertion
5. Comprehensive logging and metrics
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.cam.domain import Campaign, Lead, LeadStatus, LeadSource
from aicmo.cam.engine.lead_pipeline import (
    get_existing_leads_set,
    deduplicate_leads,
)
from aicmo.cam.ports.lead_source import LeadSourcePort

logger = logging.getLogger(__name__)


class HarvestMetrics:
    """Metrics from a harvest run."""
    
    def __init__(self):
        self.sources_tried: int = 0
        self.sources_failed: int = 0
        self.sources_succeeded: int = 0
        self.discovered: int = 0
        self.deduplicated: int = 0
        self.inserted: int = 0
        self.errors: List[str] = []
        self.start_time: datetime = datetime.utcnow()
        self.end_time: Optional[datetime] = None
    
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "sources_tried": self.sources_tried,
            "sources_failed": self.sources_failed,
            "sources_succeeded": self.sources_succeeded,
            "discovered": self.discovered,
            "deduplicated": self.deduplicated,
            "inserted": self.inserted,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds(),
        }


class HarvestOrchestrator:
    """
    Orchestrates multi-source lead harvesting.
    
    Flow:
    1. Build provider chain (ordered by preference)
    2. For each source in chain:
       - Try to fetch leads
       - If successful, deduplicate and insert
       - If failed, continue to next source (fallback)
    3. Return metrics
    
    Supports fallback chains:
    - Primary source (paid, high-quality): Apollo
    - Secondary source (free): CSV
    - Tertiary source (manual): Manual upload queue
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.metrics = HarvestMetrics()
    
    def build_provider_chain(
        self,
        campaign: Campaign,
        available_sources: Dict[str, LeadSourcePort],
        preferred_order: List[str] = None,
    ) -> List[Tuple[str, LeadSourcePort]]:
        """
        Build provider chain based on campaign settings and availability.
        
        Args:
            campaign: Campaign to build chain for
            available_sources: Dict mapping provider names to adapter instances
            preferred_order: Preferred order of providers (default: ['apollo', 'csv', 'manual'])
        
        Returns:
            List of (name, adapter) tuples in execution order
        """
        if preferred_order is None:
            preferred_order = ["apollo", "csv", "manual"]
        
        chain = []
        
        for provider_name in preferred_order:
            if provider_name in available_sources:
                adapter = available_sources[provider_name]
                if adapter.is_configured():
                    chain.append((provider_name, adapter))
                    logger.info(f"Added {provider_name} to provider chain")
                else:
                    logger.debug(f"Skipped {provider_name}: not configured")
            else:
                logger.debug(f"Unknown provider: {provider_name}")
        
        if not chain:
            logger.warning("No lead sources configured in provider chain")
        
        return chain
    
    def fetch_from_source(
        self,
        source_name: str,
        adapter: LeadSourcePort,
        campaign: Campaign,
        max_leads: int,
    ) -> Tuple[List[Lead], Optional[str]]:
        """
        Attempt to fetch leads from a single source.
        
        Args:
            source_name: Name of source (for logging)
            adapter: LeadSourcePort adapter instance
            campaign: Campaign to fetch for
            max_leads: Maximum leads to fetch
        
        Returns:
            Tuple of (leads list, error message or None)
        """
        try:
            logger.info(f"Fetching from {source_name} (max {max_leads} leads)")
            
            leads = adapter.fetch_new_leads(campaign, max_leads)
            
            logger.info(f"{source_name} returned {len(leads)} leads")
            self.metrics.sources_succeeded += 1
            
            return leads, None
        
        except Exception as e:
            error_msg = f"{source_name}: {str(e)}"
            logger.error(f"Error fetching from {source_name}: {e}")
            self.metrics.sources_failed += 1
            return [], error_msg
    
    def harvest_with_fallback(
        self,
        db: Session,
        campaign: Campaign,
        campaign_db: CampaignDB,
        provider_chain: List[Tuple[str, LeadSourcePort]],
        max_leads: int = 100,
    ) -> HarvestMetrics:
        """
        Execute harvest using provider chain with fallback logic.
        
        If primary source fails or returns <N leads, tries secondary source.
        Continues until max_leads reached or no more sources.
        
        Args:
            db: Database session
            campaign: Campaign Pydantic model
            campaign_db: Campaign database model
            provider_chain: Ordered list of (name, adapter) tuples
            max_leads: Maximum total leads to discover
        
        Returns:
            HarvestMetrics with results
        """
        logger.info(f"Starting harvest for campaign: {campaign.name}")
        
        discovered_leads = []
        existing_leads = get_existing_leads_set(db, campaign_db.id)
        
        # Try each source in order until we have enough leads
        for source_name, adapter in provider_chain:
            self.metrics.sources_tried += 1
            
            if len(discovered_leads) >= max_leads:
                logger.info(f"Reached max_leads ({max_leads}), stopping harvest")
                break
            
            # Fetch from this source
            remaining = max_leads - len(discovered_leads)
            leads, error = self.fetch_from_source(
                source_name, adapter, campaign, remaining
            )
            
            if error:
                self.metrics.errors.append(error)
                # Continue to next source (fallback)
                continue
            
            if not leads:
                logger.info(f"{source_name} returned no leads, trying next source")
                # Continue to next source
                continue
            
            # Track discovered
            self.metrics.discovered += len(leads)
            discovered_leads.extend(leads)
            
            logger.info(
                f"Total discovered so far: {self.metrics.discovered} "
                f"({len(leads)} from {source_name})"
            )
        
        logger.info(f"Harvest phase complete: {self.metrics.discovered} total discovered")
        
        # Deduplicate against existing leads
        deduplicated_leads = deduplicate_leads(discovered_leads, existing_leads)
        self.metrics.deduplicated = len(discovered_leads) - len(deduplicated_leads)
        
        logger.info(
            f"After deduplication: {len(deduplicated_leads)} new leads "
            f"({self.metrics.deduplicated} duplicates filtered)"
        )
        
        # Insert into database
        inserted = self._insert_leads_batch(
            db, campaign, campaign_db, deduplicated_leads
        )
        self.metrics.inserted = inserted
        
        # Finalize metrics
        self.metrics.end_time = datetime.utcnow()
        
        logger.info(f"Harvest complete: {self.metrics.to_dict()}")
        return self.metrics
    
    def _insert_leads_batch(
        self,
        db: Session,
        campaign: Campaign,
        campaign_db: CampaignDB,
        leads: List[Lead],
    ) -> int:
        """
        Insert leads into database.
        
        Args:
            db: Database session
            campaign: Campaign model
            campaign_db: Campaign database model
            leads: List of Lead models to insert
        
        Returns:
            Number of leads inserted
        """
        if not leads:
            return 0
        
        logger.info(f"Inserting {len(leads)} leads into database")
        
        try:
            now = datetime.utcnow()
            
            for lead in leads:
                # Create database model
                lead_db = LeadDB(
                    campaign_id=campaign_db.id,
                    name=lead.name,
                    email=lead.email,
                    company=lead.company,
                    role=lead.role,
                    linkedin_url=lead.linkedin_url,
                    status=LeadStatus.NEW,
                    source=lead.source,
                    lead_score=lead.lead_score or 0.5,
                    tags=lead.tags or [],
                    enrichment_data=lead.enrichment_data,
                    next_action_at=now,  # Ready for immediate enrichment
                )
                
                db.add(lead_db)
            
            # Commit batch
            db.commit()
            
            logger.info(f"Successfully inserted {len(leads)} leads")
            return len(leads)
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error inserting leads: {e}")
            self.metrics.errors.append(f"Insert error: {str(e)}")
            return 0


# Convenience function for direct harvesting
def run_harvest_batch(
    db: Session,
    campaign_id: int,
    lead_sources: Dict[str, LeadSourcePort],
    max_leads: int = 100,
    preferred_order: List[str] = None,
) -> HarvestMetrics:
    """
    Run a harvest batch for a campaign.
    
    Convenience function that:
    1. Loads campaign from database
    2. Builds provider chain
    3. Runs harvest with fallback
    
    Args:
        db: Database session
        campaign_id: Campaign ID to harvest for
        lead_sources: Dict of available sources {'name': adapter}
        max_leads: Maximum leads to harvest
        preferred_order: Preferred source order
    
    Returns:
        HarvestMetrics with results
    
    Raises:
        ValueError: If campaign not found
    """
    # Load campaign
    campaign_db = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign_db:
        raise ValueError(f"Campaign {campaign_id} not found")
    
    # Convert to Pydantic model
    campaign = Campaign(
        id=campaign_db.id,
        name=campaign_db.name,
        description=campaign_db.description,
        target_niche=campaign_db.target_niche,
        active=campaign_db.active,
        service_key=campaign_db.service_key,
        target_clients=campaign_db.target_clients,
        target_mrr=campaign_db.target_mrr,
        channels_enabled=campaign_db.channels_enabled,
        max_emails_per_day=campaign_db.max_emails_per_day,
    )
    
    # Build and run
    orchestrator = HarvestOrchestrator()
    provider_chain = orchestrator.build_provider_chain(
        campaign, lead_sources, preferred_order
    )
    
    if not provider_chain:
        raise ValueError("No lead sources configured")
    
    return orchestrator.harvest_with_fallback(
        db, campaign, campaign_db, provider_chain, max_leads
    )
