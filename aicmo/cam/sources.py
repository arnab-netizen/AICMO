"""
CAM lead sources.

Phase CAM-2: Import leads from CSV files and other sources.
"""

import csv
from pathlib import Path
from typing import Iterable, List

from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadSource
from aicmo.cam.db_models import LeadDB
from aicmo.domain.base import AicmoBaseModel


class CSVSourceConfig(AicmoBaseModel):
    """Configuration for importing leads from CSV file."""
    
    path: str
    campaign_id: int
    default_source: LeadSource = LeadSource.CSV


def load_leads_from_csv(config: CSVSourceConfig) -> List[Lead]:
    """
    Load leads from a CSV file.
    
    Expected CSV columns:
    - name (required) or full_name
    - company (optional)
    - role (optional) or title
    - email (optional)
    - linkedin_url (optional)
    
    Args:
        config: CSV source configuration
        
    Returns:
        List of Lead domain models
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    p = Path(config.path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {config.path}")

    leads: list[Lead] = []

    with p.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = Lead(
                campaign_id=config.campaign_id,
                name=row.get("name") or row.get("full_name") or "Unknown",
                company=row.get("company"),
                role=row.get("role") or row.get("title"),
                email=row.get("email"),
                linkedin_url=row.get("linkedin_url"),
                source=config.default_source,
            )
            leads.append(lead)
    return leads


def persist_leads(db: Session, leads: Iterable[Lead]) -> list[LeadDB]:
    """
    Persist domain Lead models to database.
    
    Args:
        db: Database session
        leads: Iterable of Lead domain models
        
    Returns:
        List of persisted LeadDB instances with IDs
    """
    rows: list[LeadDB] = []
    for lead in leads:
        row = LeadDB(
            campaign_id=lead.campaign_id,
            name=lead.name,
            company=lead.company,
            role=lead.role,
            email=lead.email,
            linkedin_url=lead.linkedin_url,
            source=lead.source,
            status=lead.status,
            notes=lead.notes,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows
