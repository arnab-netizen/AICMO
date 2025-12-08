"""
Thin wrapper around existing DB/session setup.

This allows new modules to import from aicmo.core without depending
directly on backend.* paths, making the code more portable.
"""

try:
    from backend.db.base import Base
    from backend.db.session import get_session
except ImportError:
    # Fallback for legacy imports
    from backend.db import Base, get_session  # type: ignore

# For convenience, create a SessionLocal-like factory
def SessionLocal():
    """Get a database session (generator wrapper for compatibility)."""
    return next(get_session())

__all__ = ["SessionLocal", "Base", "get_session"]
