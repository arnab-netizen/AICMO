"""
Network Egress Lock

Deny-by-default HTTP egress with allowlist for proof-run mode.
Prevents accidental external sends during E2E testing.
"""

import os
import re
from typing import List, Optional
from urllib.parse import urlparse


class EgressLock:
    """Controls network egress in E2E mode."""
    
    # Default allowlist for internal/testing hosts
    DEFAULT_ALLOWLIST = [
        r'^https?://127\.0\.0\.1',
        r'^https?://localhost',
        r'^https?://0\.0\.0\.0',
        r'^https?://.*\.local',
        r'^https?://internal\..*',
    ]
    
    def __init__(self, additional_allowlist: Optional[List[str]] = None):
        """
        Initialize egress lock.
        
        Args:
            additional_allowlist: Additional URL patterns to allow
        """
        self.enabled = os.getenv('AICMO_E2E_MODE') == '1'
        self.allowlist = self.DEFAULT_ALLOWLIST.copy()
        
        if additional_allowlist:
            self.allowlist.extend(additional_allowlist)
        
        # Load allowlist from env if provided
        env_allowlist = os.getenv('AICMO_EGRESS_ALLOWLIST', '')
        if env_allowlist:
            self.allowlist.extend(env_allowlist.split(','))
    
    def is_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed for egress.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False if blocked
        """
        if not self.enabled:
            # Egress lock disabled - allow all
            return True
        
        # Check against allowlist
        for pattern in self.allowlist:
            if re.match(pattern, url, re.IGNORECASE):
                return True
        
        # Not in allowlist - blocked
        return False
    
    def check_or_raise(self, url: str, operation: str = "network request") -> None:
        """
        Check if URL is allowed, raise exception if not.
        
        Args:
            url: URL to check
            operation: Description of operation for error message
            
        Raises:
            RuntimeError: If URL is blocked
        """
        if not self.is_allowed(url):
            raise RuntimeError(
                f"Egress blocked in E2E mode: {operation} to {url}. "
                f"Add to AICMO_EGRESS_ALLOWLIST if this is intentional."
            )
    
    def get_blocked_domains(self, attempted_urls: List[str]) -> List[str]:
        """
        Get list of blocked domains from attempted URLs.
        
        Args:
            attempted_urls: List of URLs that were attempted
            
        Returns:
            List of blocked URLs
        """
        return [url for url in attempted_urls if not self.is_allowed(url)]


# Global egress lock instance
_egress_lock: Optional[EgressLock] = None


def get_egress_lock() -> EgressLock:
    """Get global egress lock instance."""
    global _egress_lock
    if _egress_lock is None:
        _egress_lock = EgressLock()
    return _egress_lock


def check_egress_allowed(url: str) -> bool:
    """
    Check if egress to a URL is allowed.
    
    Usage:
        from aicmo.safety import check_egress_allowed
        
        if check_egress_allowed(api_url):
            response = requests.post(api_url, data=payload)
        else:
            logger.warning(f"Egress blocked: {api_url}")
    """
    lock = get_egress_lock()
    return lock.is_allowed(url)


def require_egress_allowed(url: str, operation: str = "network request") -> None:
    """
    Require egress to be allowed, raise if not.
    
    Usage:
        from aicmo.safety import require_egress_allowed
        
        require_egress_allowed(api_url, "SendGrid API call")
        response = requests.post(api_url, data=payload)
    """
    lock = get_egress_lock()
    lock.check_or_raise(url, operation)


# Monkey-patch common HTTP libraries to enforce egress lock
def patch_http_libraries():
    """
    Patch common HTTP libraries to enforce egress lock.
    Call this at application startup in E2E mode.
    """
    if os.getenv('AICMO_E2E_MODE') != '1':
        return
    
    try:
        import requests
        original_request = requests.request
        
        def locked_request(method, url, **kwargs):
            require_egress_allowed(url, f"requests.{method}")
            return original_request(method, url, **kwargs)
        
        requests.request = locked_request
    except ImportError:
        pass
    
    try:
        import urllib.request
        original_urlopen = urllib.request.urlopen
        
        def locked_urlopen(url, *args, **kwargs):
            require_egress_allowed(str(url), "urllib.request.urlopen")
            return original_urlopen(url, *args, **kwargs)
        
        urllib.request.urlopen = locked_urlopen
    except ImportError:
        pass
    
    try:
        import httpx
        original_request = httpx.request
        
        def locked_request(method, url, **kwargs):
            require_egress_allowed(str(url), f"httpx.{method}")
            return original_request(method, url, **kwargs)
        
        httpx.request = locked_request
    except ImportError:
        pass
