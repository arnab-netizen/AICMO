"""
QC module repository factory.

Creates appropriate repository based on persistence mode.
"""

from aicmo.shared.config import is_db_mode


def create_qc_repository():
    """
    Factory: Create QC repository based on AICMO_PERSISTENCE_MODE.
    
    Returns:
    - DatabaseQcRepo if mode == "db"
    - InMemoryQcRepo if mode == "inmemory" (default)
    """
    if is_db_mode():
        from aicmo.qc.internal.repositories_db import DatabaseQcRepo
        return DatabaseQcRepo()
    else:
        from aicmo.qc.internal.repositories_mem import InMemoryQcRepo
        return InMemoryQcRepo()
