"""
CAM Lead Pipeline — Lead discovery, deduplication, enrichment, and scoring.

Phase 4: Implements the lead discovery and enrichment pipeline using
LeadSourcePort and LeadEnricherPort adapters.

Steps:
1. Fetch new leads from configured sources
2. Deduplicate by email/website
3. Enrich with external data
4. Score leads
5. Persist to database
"""

from datetime import datetime
from typing import List, Dict, Set

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.cam.domain import Lead, Campaign, LeadStatus, LeadSource
from aicmo.cam.ports.lead_source import LeadSourcePort
from aicmo.cam.ports.lead_enricher import LeadEnricherPort
from aicmo.cam.ports.email_verifier import EmailVerifierPort
from aicmo.cam.engine.state_machine import (
    initial_status_for_new_lead,
    status_after_enrichment,
    compute_next_action_time,
)


# ═══════════════════════════════════════════════════════════════════════
# LEAD DISCOVERY AND DEDUPLICATION
# ═══════════════════════════════════════════════════════════════════════


def get_existing_leads_set(
    db: Session,
    campaign_id: int,
) -> Dict[str, LeadDB]:
    """
    Get set of existing leads in campaign (keyed by email).
    
    Used for deduplication.
    
    Args:
        db: Database session
        campaign_id: Campaign ID
        
    Returns:
        Dictionary mapping email to LeadDB
    """
    existing = {}
    
    leads = db.query(LeadDB).filter(LeadDB.campaign_id == campaign_id).all()
    for lead in leads:
        if lead.email:
            existing[f"email:{lead.email.lower()}"] = lead
    
    return existing


def deduplicate_leads(
    new_leads: List[Lead],
    existing_leads: Dict[str, LeadDB],
) -> List[Lead]:
    """
    Remove leads that already exist in the campaign.
    
    Args:
        new_leads: New leads discovered
        existing_leads: Dictionary of existing leads by email
        
    Returns:
        Filtered list of truly new leads
    """
    deduplicated = []
    seen = set()
    
    for lead in new_leads:
        # Check email uniqueness
        email_key = f"email:{lead.email.lower()}" if lead.email else None
        if email_key and email_key in existing_leads:
            continue  # Skip, already in DB
        if email_key and email_key in seen:
            continue  # Skip, duplicate in this batch
        if email_key:
            seen.add(email_key)
        
        deduplicated.append(lead)
    
    return deduplicated


# ═══════════════════════════════════════════════════════════════════════
# LEAD DISCOVERY
# ═══════════════════════════════════════════════════════════════════════


def fetch_and_insert_new_leads(
    db: Session,
    campaign: Campaign,
    campaign_db: CampaignDB,
    lead_sources: List[LeadSourcePort],
    max_leads: int = 50,
    now: datetime = None,
) -> int:
    """
    Discover and insert new leads from configured sources.
    
    Flow:
    1. Call each lead source adapter
    2. Collect all discovered leads
    3. Deduplicate against existing leads
    4. Set initial status to NEW
    5. Insert into database
    
    Args:
        db: Database session
        campaign: Campaign Pydantic model
        campaign_db: Campaign database model
        lead_sources: List of LeadSourcePort adapters
        max_leads: Maximum leads to discover in this run
        now: Current datetime (defaults to utcnow)
        
    Returns:
        Count of leads inserted
    """
    if now is None:
        now = datetime.utcnow()
    
    # Get existing leads for deduplication
    existing = get_existing_leads_set(db, campaign_db.id)
    
    # Discover leads from all sources
    discovered_leads = []
    for source in lead_sources:
        if not source.is_configured():
            continue
        
        try:
            leads = source.fetch_new_leads(campaign, max_leads=max_leads)
            discovered_leads.extend(leads)
        except Exception as e:
            # Log error but continue with other sources
            print(f"Error fetching from {source.get_name()}: {e}")
            continue
    
    # Limit total
    discovered_leads = discovered_leads[:max_leads]
    
    # Deduplicate
    new_leads = deduplicate_leads(discovered_leads, existing)
    
    if not new_leads:
        return 0
    
    # Insert into database
    inserted_count = 0
    for lead in new_leads:
        # Set campaign association
        lead.campaign_id = campaign_db.id
        
        # Set initial status
        lead.status = initial_status_for_new_lead(lead)
        lead.source = LeadSource.APOLLO  # Source used
        
        # Set next action time (for immediate enrichment)
        lead.next_action_at = compute_next_action_time(lead, campaign, now, "enrichment")
        
        # Convert to database model and insert
        lead_db = LeadDB(
            campaign_id=lead.campaign_id,
            name=lead.name,
            email=lead.email,
            company=lead.company,
            role=lead.role,
            linkedin_url=lead.linkedin_url,
            status=lead.status,
            source=lead.source,
            lead_score=lead.lead_score,
            tags=lead.tags or [],
            enrichment_data=lead.enrichment_data,
            next_action_at=lead.next_action_at,
        )
        
        db.add(lead_db)
        inserted_count += 1
    
    # Commit batch
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error inserting leads: {e}")
        return 0
    
    return inserted_count


# ═══════════════════════════════════════════════════════════════════════
# LEAD ENRICHMENT AND SCORING
# ═══════════════════════════════════════════════════════════════════════


def enrich_and_score_leads(
    db: Session,
    campaign: Campaign,
    campaign_db: CampaignDB,
    lead_enrichers: List[LeadEnricherPort],
    email_verifier: EmailVerifierPort,
    max_leads: int = 100,
    now: datetime = None,
) -> int:
    """
    Enrich and score leads that are due for enrichment.
    
    Flow:
    1. Find leads with status NEW and next_action_at <= now
    2. Call enricher adapters (batch if available)
    3. Verify email addresses
    4. Compute lead score (0.0-1.0)
    5. Update status to ENRICHED
    6. Update next_action_at for outreach
    7. Persist to database
    
    Args:
        db: Database session
        campaign: Campaign Pydantic model
        campaign_db: Campaign database model
        lead_enrichers: List of LeadEnricherPort adapters
        email_verifier: EmailVerifierPort adapter
        max_leads: Maximum leads to enrich in this run
        now: Current datetime (defaults to utcnow)
        
    Returns:
        Count of leads enriched
    """
    if now is None:
        now = datetime.utcnow()
    
    # Find leads due for enrichment
    leads_to_enrich = (
        db.query(LeadDB)
        .filter(
            and_(
                LeadDB.campaign_id == campaign_db.id,
                LeadDB.status == LeadStatus.NEW,
                (LeadDB.next_action_at <= now),
            )
        )
        .limit(max_leads)
        .all()
    )
    
    if not leads_to_enrich:
        return 0
    
    # Convert to Pydantic models for enrichment
    lead_models = [
        Lead(
            id=l.id,
            campaign_id=l.campaign_id,
            name=l.name,
            email=l.email,
            company=l.company,
            role=l.role,
            linkedin_url=l.linkedin_url,
            status=l.status,
            lead_score=l.lead_score,
            tags=l.tags or [],
            enrichment_data=l.enrichment_data,
            last_contacted_at=l.last_contacted_at,
            next_action_at=l.next_action_at,
        )
        for l in leads_to_enrich
    ]
    
    # Enrich via adapters (try batch first)
    enriched_models = lead_models.copy()
    for enricher in lead_enrichers:
        if not enricher.is_configured():
            continue
        
        try:
            enriched_models = enricher.enrich_batch(enriched_models)
        except Exception as e:
            print(f"Error enriching with {enricher.get_name()}: {e}")
            continue
    
    # Verify emails
    emails_to_verify = [l.email for l in enriched_models if l.email]
    verified_emails = {}
    if emails_to_verify and email_verifier.is_configured():
        try:
            verified_emails = email_verifier.verify_batch(emails_to_verify)
        except Exception as e:
            print(f"Error verifying emails: {e}")
    
    # Score leads and persist
    enriched_count = 0
    for lead_model, lead_db in zip(enriched_models, leads_to_enrich):
        # Update enrichment data
        lead_db.enrichment_data = lead_model.enrichment_data or {}
        
        # Score lead (0.0-1.0)
        # Heuristic: based on company info, job title relevance, and email validity
        score = 0.5  # Default neutral
        
        if lead_model.enrichment_data:
            # Has enrichment data → boost score
            score += 0.2
            if lead_model.enrichment_data.get("company_size"):
                score += 0.1
            if lead_model.enrichment_data.get("linkedin_url"):
                score += 0.05
        
        # Check email validity
        email_key = lead_model.email or ""
        if email_key in verified_emails:
            is_valid = verified_emails[email_key]
            if is_valid:
                score += 0.1
            else:
                score -= 0.2
        
        # Cap score at 1.0
        lead_db.lead_score = min(1.0, max(0.0, score))
        
        # Update status
        lead_db.status = status_after_enrichment(lead_model)
        
        # Set next action (for outreach)
        lead_db.next_action_at = compute_next_action_time(
            lead_model, campaign, now, "followup"
        )
        
        enriched_count += 1
    
    # Commit batch
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error persisting enriched leads: {e}")
        return 0
    
    return enriched_count
