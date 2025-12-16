"""Delivery Module - Repository Factory."""
from aicmo.shared.config import is_db_mode


def create_delivery_repository():
    """
    Create delivery repository based on persistence mode.
    
    Returns:
        DatabaseDeliveryRepo if AICMO_PERSISTENCE_MODE=db
        InMemoryDeliveryRepo if AICMO_PERSISTENCE_MODE=inmemory (default)
    """
    if is_db_mode():
        from aicmo.delivery.internal.repositories_db import DatabaseDeliveryRepo
        return DatabaseDeliveryRepo()
    else:
        from aicmo.delivery.internal.repositories_mem import InMemoryDeliveryRepo
        return InMemoryDeliveryRepo()
