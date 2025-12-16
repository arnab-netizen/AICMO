"""
E2E test fixtures and configuration.

Provides DB cleanup for tests running in DB mode.
"""

import pytest
import logging
from aicmo.shared.config import is_db_mode
from backend.db.session import get_engine
from sqlalchemy import text, inspect

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def cleanup_db_for_e2e():
    """
    Clean ALL business tables before/after each E2E test in DB mode.
    
    Uses SQLAlchemy inspector to discover tables dynamically.
    Only runs when AICMO_PERSISTENCE_MODE=db.
    Does NOT touch alembic_version table.
    
    This ensures tests are isolated and repeatable.
    """
    if not is_db_mode():
        # In-memory mode - no cleanup needed
        yield
        return
    
    # DB mode - clean all business tables
    engine = get_engine()
    
    def _clean_tables():
        """Truncate all business tables using schema inspection."""
        with engine.begin() as conn:
            dialect = engine.dialect.name
            
            if dialect == "postgresql":
                # Use SQLAlchemy inspector to get all tables
                inspector = inspect(engine)
                all_tables = inspector.get_table_names(schema='public')
                
                # Exclude system tables
                business_tables = [
                    t for t in all_tables 
                    if t not in ('alembic_version', 'spatial_ref_sys')
                ]
                
                if not business_tables:
                    logger.info("cleanup_db_for_e2e: No business tables found")
                    return
                
                # PostgreSQL: Single TRUNCATE statement with CASCADE for all tables
                # This is atomic and handles dependencies automatically
                tables_list = ', '.join(business_tables)
                truncate_sql = f"TRUNCATE TABLE {tables_list} RESTART IDENTITY CASCADE"
                
                logger.info(f"cleanup_db_for_e2e: truncating {len(business_tables)} tables: {', '.join(business_tables[:5])}{'...' if len(business_tables) > 5 else ''}")
                
                try:
                    conn.execute(text(truncate_sql))
                except Exception as e:
                    logger.error(f"cleanup_db_for_e2e: Truncate failed: {e}")
                    raise
            
            elif dialect == "sqlite":
                # SQLite: Disable FK checks, use DELETE
                inspector = inspect(engine)
                all_tables = inspector.get_table_names()
                business_tables = [t for t in all_tables if t != 'alembic_version']
                
                logger.info(f"cleanup_db_for_e2e: deleting from {len(business_tables)} tables")
                
                conn.execute(text("PRAGMA foreign_keys = OFF"))
                for table in business_tables:
                    try:
                        conn.execute(text(f"DELETE FROM {table}"))
                    except Exception:
                        pass
                conn.execute(text("PRAGMA foreign_keys = ON"))
            
            else:
                raise ValueError(f"Unsupported dialect for E2E tests: {dialect}")
    
    # Clean before test
    _clean_tables()
    
    # Run test
    yield
    
    # Clean after test (ensures cleanup even on failure)
    _clean_tables()
