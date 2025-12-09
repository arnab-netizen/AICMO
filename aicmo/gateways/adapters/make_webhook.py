"""
Make.com Webhook Adapter.

Sends CAM events (LeadCreated, LeadUpdated, OutreachEvent) to Make.com webhooks.
Optional integration for workflow automation.
"""

import logging
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class MakeWebhookAdapter:
    """
    Adapter for sending CAM events to Make.com webhooks.
    
    Allows flexible automation workflows when leads/events occur.
    Only active if MAKE_WEBHOOK_URL is configured.
    """
    
    def __init__(self):
        """Initialize Make.com adapter."""
        self.webhook_url = os.getenv("MAKE_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
    
    def send_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Send an event to Make.com webhook.
        
        Args:
            event_type: Type of event (LeadCreated, LeadUpdated, OutreachEvent, etc.)
            payload: Event data (lead, campaign, attempt, etc.)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Make.com webhook not configured, skipping {event_type}")
            return False
        
        try:
            body = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "payload": payload,
            }
            
            response = requests.post(
                self.webhook_url,
                json=body,
                timeout=10,
            )
            
            if response.status_code in (200, 201, 204):
                logger.info(f"Sent {event_type} to Make.com webhook")
                return True
            else:
                logger.warning(
                    f"Make.com webhook error ({response.status_code}): {response.text}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Make.com webhook error: {e}")
            # Non-fatal: webhook failure shouldn't block CAM operations
            return False
    
    def send_lead_created(self, lead: Dict[str, Any], campaign_name: str) -> bool:
        """
        Send LeadCreated event.
        
        Args:
            lead: Lead data
            campaign_name: Campaign name
            
        Returns:
            True if sent successfully
        """
        return self.send_event(
            "LeadCreated",
            {
                "lead": lead,
                "campaign_name": campaign_name,
            }
        )
    
    def send_lead_updated(self, lead: Dict[str, Any], changes: Dict[str, Any]) -> bool:
        """
        Send LeadUpdated event.
        
        Args:
            lead: Lead data
            changes: What changed (field -> new_value)
            
        Returns:
            True if sent successfully
        """
        return self.send_event(
            "LeadUpdated",
            {
                "lead": lead,
                "changes": changes,
            }
        )
    
    def send_outreach_event(self, lead: Dict[str, Any], attempt: Dict[str, Any]) -> bool:
        """
        Send OutreachEvent (email sent, LinkedIn message, etc.).
        
        Args:
            lead: Lead data
            attempt: Outreach attempt data
            
        Returns:
            True if sent successfully
        """
        return self.send_event(
            "OutreachEvent",
            {
                "lead": lead,
                "attempt": attempt,
            }
        )
    
    def is_configured(self) -> bool:
        """Check if Make.com webhook URL is set."""
        return self.enabled
    
    def get_name(self) -> str:
        """Return adapter name."""
        return "Make.com Webhook"
