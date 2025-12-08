"""
Proxy around existing settings.

Centralizes configuration access for the aicmo/* modules.
"""

from backend.core.config import settings

__all__ = ["settings"]
