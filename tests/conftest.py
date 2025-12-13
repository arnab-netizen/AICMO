"""
Pytest configuration and fixtures with proper test isolation.

PHASE A HARDENING: Test isolation via table truncation to prevent
database state leakage across tests. Each test gets a fresh database.
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine, event, MetaData, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aicmo.core.db import Base
# Import db_models to register tables with Base.metadata
from aicmo.cam import db_models as _  # noqa: F401

# Import shared testing fixtures from Phase 1 harness
pytest_plugins = ["aicmo.shared.testing"]


@pytest.fixture(scope="session")
def test_db_engine():
    """Create in-memory SQLite database for testing with transaction support."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    return engine


def get_all_tables(engine) -> list[str]:
    """Get all table names in the database (excluding system tables)."""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return list(metadata.tables.keys())


@pytest.fixture
def db(test_db_engine) -> Session:
    """
    Provide isolated database session for each test.
    
    PHASE A HARDENING:
    - Clears all tables before each test
    - Ensures tests cannot affect each other
    - Tests can run in any order without state leakage
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    
    # Clear all tables before test (respecting FK constraints)
    # Get tables in reverse dependency order
    tables = get_all_tables(test_db_engine)
    with test_db_engine.connect() as conn:
        # Disable FK constraint checking temporarily
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        
        # Truncate all tables
        for table in tables:
            try:
                conn.execute(text(f"DELETE FROM {table}"))
            except Exception:
                pass  # Table might not exist or might have issues
        
        # Re-enable FK constraint checking
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()
    
    yield session
    
    session.close()
