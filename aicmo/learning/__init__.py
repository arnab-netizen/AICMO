"""
AICMO Learning Module.

Provides event tracking and Kaizen continuous improvement across all subsystems.
"""

from aicmo.learning.event_types import EventType, EVENT_GROUPS, get_events_by_group
from aicmo.learning.domain import KaizenContext, KaizenInsight

__all__ = [
    "EventType",
    "EVENT_GROUPS",
    "get_events_by_group",
    "KaizenContext",
    "KaizenInsight",
]
