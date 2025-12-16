"""
delivery module.

Business responsibility: Delivery & campaign execution

Public API: api.ports, api.dtos, api.events
Internal logic: internal/*
"""

from .gate import DeliveryGate, check_delivery_allowed, block_delivery

__version__ = "1.0.0"
CONTRACT_VERSION = 1

__all__ = [
    'DeliveryGate',
    'check_delivery_allowed',
    'block_delivery',
]
