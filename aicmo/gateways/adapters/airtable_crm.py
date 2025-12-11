"""
Airtable CRM Adapter.

Implements CRMSyncer interface using Airtable's REST API v0.
Only active if AIRTABLE_API_KEY and AIRTABLE_BASE_ID are configured.
"""

import logging
import os
from typing import Dict, Optional, Any

from aicmo.gateways.interfaces import CRMSyncer
from aicmo.domain.execution import ExecutionResult, ExecutionStatus

logger = logging.getLogger(__name__)


class AirtableCRMSyncer(CRMSyncer):
    """
    CRM syncer using Airtable's API.
    
    Syncs contact data, campaign results, and engagement metrics to an Airtable base.
    Only works if AIRTABLE_API_KEY and AIRTABLE_BASE_ID are set.
    """
    
    def __init__(self):
        """Initialize Airtable CRM syncer."""
        self.api_token = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.contacts_table = os.getenv("AIRTABLE_CONTACTS_TABLE", "Contacts")
        self.interactions_table = os.getenv("AIRTABLE_INTERACTIONS_TABLE", "Interactions")
        self.api_base = "https://api.airtable.com/v0"
    
    async def sync_contact(
        self,
        email: str,
        properties: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Create or update a contact record in Airtable.
        
        Args:
            email: Contact email (unique identifier)
            properties: Contact properties to sync
            
        Returns:
            ExecutionResult with Airtable record ID or error
        """
        if not self.is_configured():
            return ExecutionResult(
                status=ExecutionStatus.SKIPPED,
                message="Airtable not configured"
            )
        
        if not email:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message="Email required"
            )
        
        try:
            import requests
            from datetime import datetime
            
            # First, try to find existing contact by email
            url = f"{self.api_base}/{self.base_id}/{self.contacts_table}"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Query for existing contact
            params = {
                "filterByFormula": f"{{Email}} = '{email}'"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            existing_records = data.get("records", [])
            
            # Prepare fields for update/create
            fields = {
                "Email": email,
                "Last Updated": datetime.now().isoformat(),
            }
            fields.update(properties)
            
            if existing_records:
                # Update existing record
                record_id = existing_records[0]["id"]
                update_url = f"{url}/{record_id}"
                
                payload = {"fields": fields}
                response = requests.patch(update_url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                
                logger.info(f"Updated Airtable contact {email}: {record_id}")
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    data={"record_id": record_id, "action": "updated"}
                )
            else:
                # Create new record
                payload = {"fields": fields}
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                
                result_data = response.json()
                record_id = result_data.get("id")
                
                logger.info(f"Created Airtable contact {email}: {record_id}")
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    data={"record_id": record_id, "action": "created"}
                )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtable sync contact API error for {email}: {e}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message=f"API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Airtable sync contact error for {email}: {e}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message=f"Sync error: {str(e)}"
            )
    
    async def log_engagement(
        self,
        contact_email: str,
        engagement_type: str,
        content_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Log an engagement event in Airtable.
        
        Args:
            contact_email: Email of contact who engaged
            engagement_type: Type (view, click, reply, etc.)
            content_id: ID of content they engaged with
            metadata: Additional engagement data
            
        Returns:
            ExecutionResult with status
        """
        if not self.is_configured():
            return ExecutionResult(
                status=ExecutionStatus.SKIPPED,
                message="Airtable not configured"
            )
        
        try:
            import requests
            from datetime import datetime
            
            # Create engagement record in Airtable
            url = f"{self.api_base}/{self.base_id}/{self.interactions_table}"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            fields = {
                "Contact Email": contact_email,
                "Engagement Type": engagement_type,
                "Content ID": content_id,
                "Timestamp": datetime.now().isoformat(),
            }
            
            if metadata:
                fields.update(metadata)
            
            payload = {"fields": fields}
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            result_data = response.json()
            record_id = result_data.get("id")
            
            logger.debug(f"Logged engagement in Airtable: {record_id}")
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data={"record_id": record_id}
            )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtable log engagement API error: {e}")
            # Engagement logging non-critical, don't fail overall
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message=f"Engagement logging failed: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Airtable log engagement error: {e}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                message=f"Engagement logging error: {str(e)}"
            )
    
    async def validate_connection(self) -> bool:
        """
        Verify Airtable connection is valid.
        
        Returns:
            True if connection works, False otherwise
        """
        if not self.is_configured():
            logger.debug("Airtable not configured")
            return False
        
        try:
            import requests
            
            # Try a simple request to verify credentials
            url = f"{self.api_base}/{self.base_id}/{self.table_id}?maxRecords=1"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            logger.info("Airtable connection validated")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Airtable connection validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Airtable connection error: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if all required Airtable credentials are set."""
        return bool(self.api_token and self.base_id)
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "Airtable CRM Syncer"
