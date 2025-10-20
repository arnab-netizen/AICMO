"""Minimal explicit re-exports for backend.db.

This file intentionally keeps the surface area small and deterministic so
test collection and imports like `from backend.db import get_db` work
reliably. It re-exports a tiny, well-defined set of helpers from the
session and utils submodules.
"""

from .session import get_engine, get_db, get_session
from .utils import ping_db, exec_sql

__all__ = ["get_engine", "get_db", "get_session", "ping_db", "exec_sql"]
