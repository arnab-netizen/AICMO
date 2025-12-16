"""
PRODUCTION API - Public contracts only.

This module exposes:
- Ports (abstract interfaces)
- DTOs (data transfer objects)
- Events (domain events)
- Models (database models - for data access layers only)
- CONTRACT_VERSION

Do NOT import from aicmo.production.internal - that violates encapsulation.
Use the exposed models and ports instead.
"""

from .contracts import CONTRACT_VERSION
from . import ports
from . import dtos
from . import events

# Expose database models for data access layers (creatives, gateways)
# These are implementation details but needed by utility layers
from ..internal.models import ProductionAssetDB

__all__ = [
    "CONTRACT_VERSION",
    "ports",
    "dtos",
    "events",
    "ProductionAssetDB",  # Exposed for data access layers
]
