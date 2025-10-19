"""
Back-compat shim: use the single canonical Asset model from `backend.models`.
This removes duplicate ORM definitions and keeps old import paths working.
"""

from backend.models import Asset

__all__ = ["Asset"]
__all__ = ["Asset"]
