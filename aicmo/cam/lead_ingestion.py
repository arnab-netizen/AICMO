"""
Lead ingestion service for CSV imports and API bulk operations.

MODULE 1: Lead Capture + Attribution
Handles deduplication, attribution tracking, and batch auditing.
"""

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from aicmo.cam.db_models import LeadDB
from aicmo.cam.import_models import ImportBatchDB
from aicmo.cam.domain import LeadSource, LeadStatus


@dataclass
class ImportResult:
    """Result of a lead import operation."""
    batch_id: int
    total_rows: int
    successful_imports: int
    failed_imports: int
    duplicate_skips: int
    errors: List[str]


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file for deduplication."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_duplicate_import(session: Session, file_hash: str) -> Optional[ImportBatchDB]:
    """Check if this file was already imported."""
    return session.query(ImportBatchDB).filter_by(file_hash=file_hash).first()


def deduplicate_lead(
    session: Session,
    email: Optional[str],
    campaign_id: Optional[int],
    identity_hash: Optional[str]
) -> bool:
    """
    Check if lead already exists.
    
    Deduplication rules:
    1. If email + campaign_id exists -> duplicate
    2. If identity_hash exists (cross-campaign) -> duplicate
    3. Otherwise -> new lead
    
    Returns True if duplicate found.
    """
    if email and campaign_id:
        existing = session.query(LeadDB).filter_by(
            email=email,
            campaign_id=campaign_id
        ).first()
        if existing:
            return True
    
    if identity_hash:
        existing = session.query(LeadDB).filter_by(
            identity_hash=identity_hash
        ).first()
        if existing:
            return True
    
    return False


def import_leads_from_csv(
    session: Session,
    file_path: Path,
    campaign_id: Optional[int],
    venture_id: Optional[str],
    uploaded_by: str,
    source_system: Optional[str] = None,
    source_list_name: Optional[str] = None
) -> ImportResult:
    """
    Import leads from CSV file with full attribution tracking.
    
    Expected CSV columns:
    - name (required)
    - email (optional but recommended)
    - company (optional)
    - role (optional)
    - linkedin_url (optional)
    - utm_source (optional)
    - utm_medium (optional)
    - utm_campaign (optional)
    - landing_page (optional)
    - ref_code (optional)
    - source_notes (optional)
    
    Args:
        session: Database session
        file_path: Path to CSV file
        campaign_id: Campaign to associate leads with
        venture_id: Venture (client) these leads belong to
        uploaded_by: Operator email or API identifier
        source_system: Where leads came from (e.g., "apollo", "manual_entry")
        source_list_name: Human-readable name for this batch
    
    Returns:
        ImportResult with batch_id and statistics
    """
    
    # Calculate file hash for duplicate detection
    file_hash = calculate_file_hash(file_path)
    
    # Check if already imported
    duplicate_batch = check_duplicate_import(session, file_hash)
    if duplicate_batch:
        return ImportResult(
            batch_id=duplicate_batch.id,
            total_rows=0,
            successful_imports=0,
            failed_imports=0,
            duplicate_skips=0,
            errors=[f"File already imported in batch {duplicate_batch.id}"]
        )
    
    # Create import batch record
    batch = ImportBatchDB(
        file_name=file_path.name,
        file_hash=file_hash,
        uploaded_by=uploaded_by,
        source_system=source_system or "csv_import",
        source_list_name=source_list_name or file_path.stem,
        campaign_id=campaign_id,
        venture_id=venture_id
    )
    session.add(batch)
    session.flush()  # Get batch.id
    
    # Parse CSV
    successful = 0
    failed = 0
    duplicates = 0
    errors = []
    total_rows = 0
    
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            total_rows += 1
            
            try:
                # Required field validation
                if not row.get('name'):
                    errors.append(f"Row {row_num}: Missing required field 'name'")
                    failed += 1
                    continue
                
                # Generate identity hash for deduplication
                email = row.get('email', '').strip() or None
                identity_hash = None
                if email:
                    identity_hash = hashlib.sha256(
                        f"{email.lower()}".encode()
                    ).hexdigest()[:16]
                
                # Check for duplicates
                if deduplicate_lead(session, email, campaign_id, identity_hash):
                    duplicates += 1
                    continue
                
                # Create lead with full attribution
                lead = LeadDB(
                    campaign_id=campaign_id,
                    venture_id=venture_id,
                    name=row['name'].strip(),
                    email=email,
                    company=row.get('company', '').strip() or None,
                    role=row.get('role', '').strip() or None,
                    linkedin_url=row.get('linkedin_url', '').strip() or None,
                    
                    # Attribution fields (MODULE 1)
                    source=LeadSource.CSV,
                    status=LeadStatus.NEW,
                    source_channel=source_system or "csv_import",
                    source_ref=f"batch_{batch.id}_row_{row_num}",
                    utm_campaign=row.get('utm_campaign', '').strip() or None,
                    utm_content=row.get('utm_content', '').strip() or None,
                    
                    # Additional attribution metadata
                    notes=row.get('source_notes', '').strip() or None,
                    identity_hash=identity_hash,
                    consent_status="UNKNOWN",  # Default, must be explicitly set
                    
                    first_touch_at=datetime.now(timezone.utc)
                )
                
                session.add(lead)
                successful += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                failed += 1
                continue
    
    # Update batch statistics
    batch.total_rows = total_rows
    batch.successful_imports = successful
    batch.failed_imports = failed
    batch.duplicate_skips = duplicates
    if errors:
        batch.error_log = "\n".join(errors)
    
    session.commit()
    
    return ImportResult(
        batch_id=batch.id,
        total_rows=total_rows,
        successful_imports=successful,
        failed_imports=failed,
        duplicate_skips=duplicates,
        errors=errors
    )


def import_leads_from_api(
    session: Session,
    leads_data: List[Dict[str, Any]],
    campaign_id: Optional[int],
    venture_id: Optional[str],
    uploaded_by: str,
    source_system: str,
    source_list_name: Optional[str] = None
) -> ImportResult:
    """
    Import leads from API payload (bulk operation).
    
    Similar to CSV import but accepts list of dicts instead of file.
    
    Args:
        session: Database session
        leads_data: List of lead dictionaries
        campaign_id: Campaign to associate leads with
        venture_id: Venture these leads belong to
        uploaded_by: API key or operator identifier
        source_system: Origin system (e.g., "apollo_api", "webhook")
        source_list_name: Human-readable batch name
    
    Returns:
        ImportResult with statistics
    """
    
    # Create import batch record
    batch = ImportBatchDB(
        file_name=None,  # No file for API imports
        file_hash=None,
        uploaded_by=uploaded_by,
        source_system=source_system,
        source_list_name=source_list_name or f"API_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        campaign_id=campaign_id,
        venture_id=venture_id
    )
    session.add(batch)
    session.flush()
    
    successful = 0
    failed = 0
    duplicates = 0
    errors = []
    total_rows = len(leads_data)
    
    for idx, lead_dict in enumerate(leads_data):
        try:
            # Required field validation
            if not lead_dict.get('name'):
                errors.append(f"Item {idx}: Missing required field 'name'")
                failed += 1
                continue
            
            # Generate identity hash
            email = lead_dict.get('email', '').strip() or None
            identity_hash = None
            if email:
                identity_hash = hashlib.sha256(
                    f"{email.lower()}".encode()
                ).hexdigest()[:16]
            
            # Check duplicates
            if deduplicate_lead(session, email, campaign_id, identity_hash):
                duplicates += 1
                continue
            
            # Create lead
            lead = LeadDB(
                campaign_id=campaign_id,
                venture_id=venture_id,
                name=lead_dict['name'].strip(),
                email=email,
                company=lead_dict.get('company', '').strip() or None,
                role=lead_dict.get('role', '').strip() or None,
                linkedin_url=lead_dict.get('linkedin_url', '').strip() or None,
                
                source=LeadSource.APOLLO,  # API imports typically from external sources
                status=LeadStatus.NEW,
                source_channel=source_system,
                source_ref=f"batch_{batch.id}_item_{idx}",
                utm_campaign=lead_dict.get('utm_campaign', '').strip() or None,
                utm_content=lead_dict.get('utm_content', '').strip() or None,
                
                notes=lead_dict.get('notes', '').strip() or None,
                identity_hash=identity_hash,
                consent_status=lead_dict.get('consent_status', 'UNKNOWN'),
                
                first_touch_at=datetime.now(timezone.utc)
            )
            
            session.add(lead)
            successful += 1
            
        except Exception as e:
            errors.append(f"Item {idx}: {str(e)}")
            failed += 1
            continue
    
    # Update batch statistics
    batch.total_rows = total_rows
    batch.successful_imports = successful
    batch.failed_imports = failed
    batch.duplicate_skips = duplicates
    if errors:
        batch.error_log = "\n".join(errors)
    
    session.commit()
    
    return ImportResult(
        batch_id=batch.id,
        total_rows=total_rows,
        successful_imports=successful,
        failed_imports=failed,
        duplicate_skips=duplicates,
        errors=errors
    )
