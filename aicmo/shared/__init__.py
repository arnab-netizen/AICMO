"""
AICMO Shared module.

Contains only generic, non-business utilities:
- Config: Environment-based settings (persistence mode, etc.)
- Testing harness (fixtures, fake providers)
- Clock and time utilities
- ID generation (ULID, UUID)
- Error base classes
- Serialization utilities

No business logic allowed here.
"""

__version__ = "1.0.0"

from aicmo.shared.config import (
    settings,
    is_db_mode,
    is_inmemory_mode,
    is_test_mode,
)

__all__ = [
    "settings",
    "is_db_mode",
    "is_inmemory_mode",
    "is_test_mode",
    "testing",
]

