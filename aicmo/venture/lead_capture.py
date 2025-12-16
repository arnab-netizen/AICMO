"""
Lead capture service with identity resolution and deduplication.

MODULE 1: Foundation for lead management.
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import or_

from aicmo.cam.db_models import LeadDB


@dataclass
class LeadCaptureRequest:
    """Request to capture a new lead."""
    venture_id: str
    campaign_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    source_channel: Optional[str] = None
    source_ref: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    consent_status: str = "UNKNOWN"  # UNKNOWN, CONSENTED, DNC
    notes: Optional[str] = None


def generate_identity_hash(email: Optional[str], phone: Optional[str], linkedin_url: Optional[str]) -> str:
    """
    Generate unique identity hash for deduplication.
    
    Uses available contact info to create a consistent hash.
    Multiple records with same contact info will have same hash.
    """
    # Normalize inputs
    parts = []
    if email:
        parts.append(f"email:{email.lower().strip()}")
    if phone:
        # Remove common formatting
        clean_phone = ''.join(c for c in phone if c.isdigit())
        if clean_phone:
            parts.append(f"phone:{clean_phone}")
    if linkedin_url:
        parts.append(f"linkedin:{linkedin_url.lower().strip()}")
    
    if not parts:
        # No contact info - generate random hash (will not dedupe)
        parts.append(f"random:{datetime.now(timezone.utc).isoformat()}")
    
    identity_string = "|".join(sorted(parts))
    return hashlib.sha256(identity_string.encode()).hexdigest()


def capture_lead(session: Session, request: LeadCaptureRequest) -> LeadDB:
    """
    Capture a lead with deduplication.
    
    If lead with same identity_hash exists:
    - Update touch timestamps
    - Do NOT create duplicate
    
    Returns:
        LeadDB: New or existing lead
    """
    # Generate identity hash
    identity_hash = generate_identity_hash(request.email, request.phone, request.linkedin_url)
    
    # Check for existing lead with same identity
    existing = session.query(LeadDB).filter(
        LeadDB.identity_hash == identity_hash,
        LeadDB.venture_id == request.venture_id
    ).first()
    
    now = datetime.now(timezone.utc)
    
    if existing:
        # Update touch timestamps (lead came back)
        existing.last_touch_at = now
        if not existing.first_touch_at:
            existing.first_touch_at = now
        
        # Update campaign if different
        if existing.campaign_id != request.campaign_id:
            existing.campaign_id = request.campaign_id
        
        session.commit()
        return existing
    
    # Create new lead
    lead = LeadDB(
        venture_id=request.venture_id,
        campaign_id=request.campaign_id,
        name=request.name,
        email=request.email,
        linkedin_url=request.linkedin_url,
        company=request.company,
        role=request.role,
        identity_hash=identity_hash,
        consent_status=request.consent_status,
        consent_date=now if request.consent_status == "CONSENTED" else None,
        source_channel=request.source_channel,
        source_ref=request.source_ref,
        utm_campaign=request.utm_campaign,
        utm_content=request.utm_content,
        first_touch_at=now,
        last_touch_at=now,
        notes=request.notes
    )
    
    session.add(lead)
    session.commit()
    return lead


def mark_lead_dnc(session: Session, lead_id: int) -> None:
    """
    Mark lead as Do Not Contact (DNC).
    
    This is a hard block - lead will never be contacted again.
    """
    lead = session.query(LeadDB).filter_by(id=lead_id).first()
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")
    
    lead.consent_status = "DNC"
    session.commit()


def is_contactable(session: Session, lead_id: int) -> bool:
    """
    Check if lead can be contacted.
    
    Returns False if:
    - Lead has DNC status
    - Lead doesn't exist
    """
    lead = session.query(LeadDB).filter_by(id=lead_id).first()
    if not lead:
        return False
    
    return lead.consent_status != "DNC"
