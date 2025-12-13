"""
AICMO Shared module.

Contains only generic, non-business utilities:
- Testing harness (fixtures, fake providers)
- Clock and time utilities
- ID generation (ULID, UUID)
- Error base classes
- Serialization utilities

No business logic allowed here.
"""

__version__ = "1.0.0"

__all__ = [
    "testing",
]
