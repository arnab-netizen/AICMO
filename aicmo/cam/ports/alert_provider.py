"""
Alert provider interface for CAM autonomous worker.

Pluggable interface for sending alerts to humans on important events
(e.g., positive replies, campaign auto-pause).
"""

from typing import Protocol, Dict, Any, Optional


class AlertProvider(Protocol):
    """Protocol for alert providers."""
    
    def send_alert(
        self,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send an alert.
        
        Args:
            title: Short alert title
            message: Alert message body
            metadata: Additional context (lead_id, email, etc.)
        
        Returns:
            True if alert sent successfully, False otherwise
        """
        ...
    
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        ...
    
    def get_name(self) -> str:
        """Get provider name for logging."""
        ...
