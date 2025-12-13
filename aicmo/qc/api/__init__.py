"""
QC API - Public contracts only.

This module exposes:
- Ports (abstract interfaces)
- DTOs (data transfer objects)
- Events (domain events)
- CONTRACT_VERSION

Do NOT import from aicmo.qc.internal - that violates encapsulation.
"""

from .contracts import CONTRACT_VERSION
from . import ports
from . import dtos
from . import events

__all__ = [
    "CONTRACT_VERSION",
    "ports",
    "dtos",
    "events",
]
