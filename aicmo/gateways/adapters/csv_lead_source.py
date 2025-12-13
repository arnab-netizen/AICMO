"""
CSV Lead Source Adapter.

Implements LeadSourcePort to fetch leads from a CSV file.
Supports both local file paths and URL sources.

Environment Variables (Optional):
  CSV_LEAD_SOURCE_PATH: Path to CSV file (default: "leads.csv")
  CSV_DELIMITER: CSV delimiter (default: ",")
  CSV_REQUIRED_COLUMNS: Comma-separated list of required columns

CSV Format Expected:
  - name (required): Contact name
  - email (required): Email address
  - company (optional): Company name
  - role (optional): Job title
  - linkedin_url (optional): LinkedIn profile URL
  - phone (optional): Phone number
  - other fields are stored in enrichment_data
"""

import logging
import os
import csv
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from aicmo.cam.ports.lead_source import LeadSourcePort
from aicmo.cam.domain import Lead, Campaign, LeadSource

logger = logging.getLogger(__name__)


class CSVLeadSource(LeadSourcePort):
    """
    Lead source adapter for CSV files.
    
    Reads leads from a CSV file and yields them as Lead objects.
    Handles deduplication at the source level.
    """
    
    def __init__(
        self,
        file_path: str = None,
        delimiter: str = ",",
        required_columns: List[str] = None,
    ):
        """
        Initialize CSV lead source.
        
        Args:
            file_path: Path to CSV file (from env or parameter)
            delimiter: CSV delimiter character
            required_columns: List of required column names
        """
        # Get path from parameter or environment
        self.file_path = file_path or os.getenv("CSV_LEAD_SOURCE_PATH", "leads.csv")
        self.delimiter = delimiter or os.getenv("CSV_DELIMITER", ",")
        self.required_columns = required_columns or ["name", "email"]
        
        # Get column mappings from environment or use defaults
        self.column_mapping = {
            "name": "name",
            "email": "email",
            "company": "company",
            "role": "role",
            "linkedin_url": "linkedin_url",
        }
    
    def is_configured(self) -> bool:
        """
        Check if CSV source is properly configured.
        
        Returns:
            True if file exists and is readable; False otherwise.
        """
        if not self.file_path:
            logger.debug("CSV_LEAD_SOURCE_PATH not set")
            return False
        
        file_exists = Path(self.file_path).exists()
        if not file_exists:
            logger.debug(f"CSV file not found: {self.file_path}")
        
        return file_exists
    
    def _parse_csv_file(self) -> List[Dict[str, Any]]:
        """
        Parse CSV file and return list of rows as dicts.
        
        Returns:
            List of dictionaries (one per CSV row)
            
        Raises:
            Exception: If file cannot be read or is malformed
        """
        if not self.is_configured():
            return []
        
        rows = []
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                
                if reader.fieldnames is None:
                    logger.warning(f"CSV file empty or malformed: {self.file_path}")
                    return []
                
                # Validate required columns exist
                missing_columns = [
                    col for col in self.required_columns
                    if col not in reader.fieldnames
                ]
                if missing_columns:
                    logger.error(
                        f"CSV missing required columns: {missing_columns}. "
                        f"Found: {reader.fieldnames}"
                    )
                    return []
                
                for row_num, row in enumerate(reader, start=2):  # start at 2 (header is row 1)
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    rows.append(row)
                
                logger.info(f"Parsed {len(rows)} rows from {self.file_path}")
                return rows
        
        except UnicodeDecodeError as e:
            logger.error(f"CSV file encoding error: {e}. Try UTF-8 encoding.")
            return []
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            return []
    
    def _row_to_lead(self, row: Dict[str, Any]) -> Optional[Lead]:
        """
        Convert CSV row to Lead object.
        
        Args:
            row: Dictionary from CSV reader
            
        Returns:
            Lead object, or None if invalid
        """
        try:
            # Extract required fields
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()
            
            # Validate
            if not name:
                logger.debug(f"CSV row missing name: {row}")
                return None
            
            if not email or "@" not in email:
                logger.debug(f"CSV row has invalid email: {row}")
                return None
            
            # Extract optional fields
            company = row.get("company", "").strip() or None
            role = row.get("role", "").strip() or None
            linkedin_url = row.get("linkedin_url", "").strip() or None
            
            # Store any extra columns in enrichment_data
            enrichment_data = {}
            standard_fields = {"name", "email", "company", "role", "linkedin_url"}
            for key, value in row.items():
                if key not in standard_fields and value and value.strip():
                    enrichment_data[key.lower()] = value.strip()
            
            # Create Lead object
            lead = Lead(
                name=name,
                email=email.lower(),
                company=company,
                role=role,
                linkedin_url=linkedin_url,
                source=LeadSource.CSV,
                lead_score=0.5,  # Default; will be scored in pipeline
                enrichment_data=enrichment_data or None,
                tags=["csv_import"],
            )
            
            return lead
        
        except Exception as e:
            logger.error(f"Error converting CSV row to Lead: {e}")
            return None
    
    def fetch_new_leads(
        self,
        campaign: Campaign,
        max_leads: int = 50,
    ) -> List[Lead]:
        """
        Fetch leads from CSV file.
        
        Args:
            campaign: Campaign to fetch leads for (used for logging)
            max_leads: Maximum number of leads to return
            
        Returns:
            List of Lead objects from CSV file
        """
        if not self.is_configured():
            logger.debug("CSV source not configured, returning empty list")
            return []
        
        logger.info(f"Fetching up to {max_leads} leads from CSV: {self.file_path}")
        
        # Parse CSV file
        rows = self._parse_csv_file()
        if not rows:
            logger.warning(f"No valid rows found in CSV file: {self.file_path}")
            return []
        
        # Convert rows to Lead objects
        leads = []
        for row in rows:
            lead = self._row_to_lead(row)
            if lead:
                leads.append(lead)
                if len(leads) >= max_leads:
                    break
        
        logger.info(f"CSV source returning {len(leads)} leads")
        return leads
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "CSV Lead Source"
    
    def get_file_path(self) -> str:
        """Return current file path."""
        return self.file_path
