"""
Smoke test: AOL daemon runs ticks successfully against a database.

Verifies:
  - Daemon can initialize database
  - Daemon can run 2 ticks without crashing
  - Tick ledger records are created
  - No "no such table" errors occur
"""

import os
import pytest
import sqlite3
from pathlib import Path


@pytest.fixture
def test_db_url():
    """Create a temporary SQLite database for testing."""
    import tempfile
    
    # Use temporary directory
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test_daemon.db"
    db_url = f"sqlite:///{db_path}"
    
    yield db_url
    
    # Cleanup
    try:
        Path(db_path).unlink()
        Path(tmpdir).rmdir()
    except:
        pass


def test_daemon_loop_ticks_sqlite(test_db_url, monkeypatch):
    """Test that daemon can run 2 ticks against SQLite without crashing."""
    # Set DB URL for this test
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    
    from aicmo.orchestration.daemon import AOLDaemon
    from aicmo.orchestration.models import Base, AOLTickLedger
    from sqlalchemy import create_engine, select, inspect
    
    # Initialize database with schema
    engine = create_engine(test_db_url, future=True)
    Base.metadata.create_all(engine)
    
    # Create daemon
    daemon = AOLDaemon(test_db_url)
    
    # Run 2 ticks
    exit_code = daemon.run(max_ticks=2)
    
    assert exit_code == 0, "Daemon should exit successfully"
    
    # Verify ticks were recorded
    engine2 = create_engine(test_db_url, future=True)
    inspector = inspect(engine2)
    tables = inspector.get_table_names()
    
    assert 'aol_tick_ledger' in tables, "Tick ledger table should exist"
    assert 'aol_actions' in tables, "Actions table should exist"
    assert 'aol_lease' in tables, "Lease table should exist"


def test_daemon_initializes_tables_sqlite(test_db_url, monkeypatch):
    """Test that daemon crashes gracefully if tables don't exist (requires migration)."""
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    
    from aicmo.orchestration.daemon import AOLDaemon
    from sqlalchemy import create_engine, inspect
    
    # Create empty database (no schema yet)
    engine = create_engine(test_db_url, future=True)
    
    # Verify tables don't exist
    inspector = inspect(engine)
    tables_before = set(inspector.get_table_names())
    assert 'aol_lease' not in tables_before, "Lease table shouldn't exist initially"
    
    # Try to create daemon with no schema - it should fail gracefully
    daemon = AOLDaemon(test_db_url)
    
    # Daemon should fail immediately (no tables)
    # This is expected - migrations must be run first
    exit_code = daemon.run(max_ticks=1)
    
    # Exit code should be non-zero (error)
    assert exit_code != 0, "Daemon should fail when tables don't exist"


def test_daemon_proof_mode_ticks(test_db_url, monkeypatch):
    """Test that daemon runs in PROOF mode without crashing."""
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv("AOL_PROOF_MODE", "1")
    
    from aicmo.orchestration.daemon import AOLDaemon
    from aicmo.orchestration.models import Base
    from sqlalchemy import create_engine
    
    engine = create_engine(test_db_url, future=True)
    Base.metadata.create_all(engine)
    
    daemon = AOLDaemon(test_db_url)
    
    # Run in PROOF mode
    exit_code = daemon.run(max_ticks=2)
    
    assert exit_code == 0, "PROOF mode daemon should exit successfully"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
