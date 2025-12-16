"""
Secure structured logging with secret redaction.

Ensures secrets never leak into logs.
"""

import logging
import re
from typing import Any, Dict
from datetime import datetime


# Patterns to redact (case-insensitive)
SECRET_PATTERNS = [
    r'api[_-]?key',
    r'password',
    r'secret',
    r'token',
    r'auth',
    r'bearer',
    r'credential',
    r'private[_-]?key',
]

# Compiled regex for efficiency
SECRET_REGEX = re.compile('|'.join(SECRET_PATTERNS), re.IGNORECASE)


def redact_secrets(data: Any) -> Any:
    """
    Recursively redact secrets from data structures.
    
    Args:
        data: Dictionary, list, or primitive to redact
        
    Returns:
        Redacted copy of data
    """
    if isinstance(data, dict):
        return {
            key: '***REDACTED***' if SECRET_REGEX.search(str(key)) else redact_secrets(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    elif isinstance(data, str):
        # Check if entire string looks like a secret value
        if len(data) > 20 and any(char in data for char in ['/', '_', '-', '=']):
            # Heuristic: long strings with special chars might be tokens
            return '***REDACTED***'
        return data
    else:
        return data


class SecureLogger:
    """
    Logger wrapper that redacts secrets.
    
    Usage:
        logger = SecureLogger(__name__)
        logger.info("Processing campaign", campaign_id=123, api_key="secret")
        # Logs: "Processing campaign" with campaign_id=123, api_key=***REDACTED***
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with secret redaction."""
        # Redact kwargs
        safe_kwargs = redact_secrets(kwargs)
        
        # Format message with context
        if safe_kwargs:
            context_str = ' '.join(f"{k}={v}" for k, v in safe_kwargs.items())
            full_message = f"{message} | {context_str}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)


def configure_campaign_logging(campaign_id: int, venture_id: str, run_id: str):
    """
    Configure logging with campaign context.
    
    Sets up log format to include campaign_id, venture_id, run_id.
    
    Args:
        campaign_id: Campaign identifier
        venture_id: Venture identifier
        run_id: Unique run identifier
    """
    # Create formatter with context
    formatter = logging.Formatter(
        f'%(asctime)s - %(name)s - %(levelname)s - '
        f'[campaign={campaign_id} venture={venture_id} run={run_id}] - '
        f'%(message)s'
    )
    
    # Apply to all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
