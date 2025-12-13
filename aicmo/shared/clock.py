"""
Clock abstraction for deterministic time handling in contracts.

Use ClockPort instead of datetime.now() in business logic to enable:
- Time-travel testing
- Fixed-time scenarios
- Timezone-aware operations
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Abstract clock interface for time operations."""
    
    def now(self) -> datetime:
        """Get current datetime (timezone-aware UTC)."""
        ...
    
    def timestamp(self) -> float:
        """Get current Unix timestamp."""
        ...


class SystemClock:
    """Production clock using system time."""
    
    def now(self) -> datetime:
        """Get current datetime in UTC."""
        from datetime import timezone
        return datetime.now(timezone.utc)
    
    def timestamp(self) -> float:
        """Get current Unix timestamp."""
        return self.now().timestamp()


class FixedClock:
    """Test clock with fixed time (from Phase 1 harness)."""
    
    def __init__(self, fixed_time: datetime):
        self._fixed_time = fixed_time
    
    def now(self) -> datetime:
        """Return fixed datetime."""
        return self._fixed_time
    
    def timestamp(self) -> float:
        """Return fixed timestamp."""
        return self._fixed_time.timestamp()


__all__ = ["ClockPort", "SystemClock", "FixedClock"]
