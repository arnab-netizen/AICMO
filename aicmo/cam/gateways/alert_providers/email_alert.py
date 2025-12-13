"""
Email alert provider using Resend API.

Sends urgent alerts to humans via email.
"""

import os
import logging
from typing import Dict, Any, Optional

from aicmo.cam.gateways.email_providers.resend import ResendEmailProvider
from aicmo.cam.config import CamSettings

logger = logging.getLogger(__name__)


class EmailAlertProvider:
    """Send alerts via Resend email."""
    
    def __init__(self):
        settings = CamSettings()
        self.resend_provider = ResendEmailProvider(
            api_key=settings.RESEND_API_KEY,
            from_email=settings.RESEND_FROM_EMAIL,
            dry_run=False,
        )
        self.alert_emails = os.getenv('AICMO_CAM_ALERT_EMAILS', '').split(',')
        self.alert_emails = [e.strip() for e in self.alert_emails if e.strip()]
        self.from_email = settings.RESEND_FROM_EMAIL
    
    def send_alert(
        self,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send alert email to configured recipients."""
        
        if not self.is_configured():
            logger.warning("Email alert provider not configured (no recipient emails)")
            return False
        
        try:
            metadata = metadata or {}
            
            # Format email body
            body = f"""
🚨 CAM ALERT 🚨

{title}

────────────────────────────────────────

{message}

────────────────────────────────────────

Metadata:
{self._format_metadata(metadata)}

────────────────────────────────────────

This is an automated alert from CAM autonomous worker.
"""
            
            subject = f"🚨 {title}"
            
            # Send to all alert recipients
            sent_count = 0
            for recipient in self.alert_emails:
                try:
                    result = self.resend_provider.send(
                        to_email=recipient,
                        from_email=self.from_email,
                        subject=subject,
                        html_body=self._html_format(title, message, metadata),
                        custom_headers={
                            'X-Alert-Type': 'CAM',
                            'X-Alert-Level': 'URGENT',
                        },
                    )
                    
                    if result.success:
                        logger.info(f"✓ Alert sent to {recipient}")
                        sent_count += 1
                    else:
                        logger.error(f"✗ Alert failed for {recipient}: {result.error}")
                
                except Exception as e:
                    logger.error(f"✗ Error sending alert to {recipient}: {str(e)}")
            
            return sent_count > 0
        
        except Exception as e:
            logger.error(f"✗ Alert send failed: {str(e)}", exc_info=True)
            return False
    
    def is_configured(self) -> bool:
        """Check if alert provider is configured."""
        return (
            self.resend_provider.is_configured() and
            len(self.alert_emails) > 0
        )
    
    def get_name(self) -> str:
        """Get provider name."""
        return "EmailAlert"
    
    def health(self) -> dict:
        """Return health status of alert module."""
        from aicmo.cam.contracts import ModuleHealthModel
        try:
            configured = self.is_configured()
            return ModuleHealthModel(
                module_name="AlertModule",
                is_healthy=configured,
                status="READY" if configured else "DISABLED",
                message="Alert provider configured" if configured else "Alert not configured"
            ).dict()
        except Exception as e:
            return ModuleHealthModel(
                module_name="AlertModule",
                is_healthy=False,
                status="ERROR",
                message=str(e)
            ).dict()
    
    @staticmethod
    def _format_metadata(metadata: Dict[str, Any]) -> str:
        """Format metadata for email."""
        if not metadata:
            return "(none)"
        
        lines = []
        for key, value in metadata.items():
            lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _html_format(title: str, message: str, metadata: Dict[str, Any]) -> str:
        """Format as HTML for email."""
        metadata_html = "".join(
            f"<tr><td style='padding: 5px; font-family: monospace;'><b>{k}:</b></td>"
            f"<td style='padding: 5px; font-family: monospace;'>{v}</td></tr>"
            for k, v in (metadata or {}).items()
        )
        
        return f"""
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="background-color: #fff3cd; border: 2px solid #ff6b6b; padding: 20px; border-radius: 5px;">
        <h2 style="color: #ff6b6b; margin-top: 0;">🚨 {title}</h2>
        
        <div style="background-color: white; padding: 15px; margin: 10px 0; border-radius: 3px;">
            <pre style="white-space: pre-wrap; word-wrap: break-word;">{message}</pre>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; background-color: #f8f9fa;">
            {metadata_html}
        </table>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="font-size: 12px; color: #666;">
            This is an automated alert from CAM autonomous worker.
        </p>
    </div>
</body>
</html>
"""


class NoOpAlertProvider:
    """No-op alert provider (safe fallback)."""
    
    def send_alert(
        self,
        title: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Silently ignore alert."""
        logger.debug(f"[NoOp] Alert (not sent): {title}")
        return True
    
    def is_configured(self) -> bool:
        """Always configured."""
        return True
    
    def get_name(self) -> str:
        """Get provider name."""
        return "NoOp"
    
    def health(self) -> dict:
        """Return health status of no-op alert module."""
        from aicmo.cam.contracts import ModuleHealthModel
        return ModuleHealthModel(
            module_name="AlertModule",
            is_healthy=True,
            status="READY",
            message="No-op alert provider (alerts not sent)"
        ).dict()
