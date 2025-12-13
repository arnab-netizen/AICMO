"""
Alert provider factory for plugin selection.
"""

import os
import logging
from typing import Union

from aicmo.cam.gateways.alert_providers.email_alert import (
    EmailAlertProvider,
    NoOpAlertProvider,
)

logger = logging.getLogger(__name__)


def get_alert_provider() -> Union[EmailAlertProvider, NoOpAlertProvider]:
    """
    Get configured alert provider.
    
    Selection logic:
    - If AICMO_CAM_ALERT_EMAILS is set → EmailAlertProvider
    - Else → NoOpAlertProvider (safe fallback)
    
    Returns:
        Configured alert provider instance
    """
    
    alert_emails = os.getenv('AICMO_CAM_ALERT_EMAILS', '').strip()
    
    if alert_emails:
        logger.info("Using EmailAlertProvider")
        return EmailAlertProvider()
    
    logger.info("Using NoOpAlertProvider (AICMO_CAM_ALERT_EMAILS not set)")
    return NoOpAlertProvider()
