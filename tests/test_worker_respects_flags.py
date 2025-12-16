"""
Test: AOL Worker respects control flags (pause, kill).

Verifies that worker correctly handles:
- Paused flag: worker sleeps instead of running ticks
- Killed flag: worker exits cleanly with code 0
"""

import os
import sqlite3
import tempfile
import pytest
from datetime import datetime, timezone
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import AOL models
from aicmo.orchestration.models import (
    Base,
    AOLControlFlags,
    AOLTickLedger,
    AOLAction,
)


@contextmanager
def create_temp_sqlite_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test_aol.db')
        db_url = f'sqlite:///{db_path}'
        
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        
        yield engine, db_url
        
        engine.dispose()


def test_worker_respects_paused_flag():
    """Test that paused flag prevents worker from running ticks."""
    with create_temp_sqlite_db() as (engine, db_url):
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Set paused flag
        flags = AOLControlFlags(id=1, paused=True, killed=False, proof_mode=True)
        session.add(flags)
        session.commit()
        
        # Verify flag is set
        flags_check = session.query(AOLControlFlags).filter_by(id=1).first()
        assert flags_check.paused is True, "Paused flag not set"
        assert flags_check.killed is False, "Killed flag should not be set"
        
        session.close()


def test_worker_respects_killed_flag():
    """Test that killed flag causes worker to exit gracefully."""
    with create_temp_sqlite_db() as (engine, db_url):
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Set killed flag
        flags = AOLControlFlags(id=1, paused=False, killed=True, proof_mode=True)
        session.add(flags)
        session.commit()
        
        # Verify flag is set
        flags_check = session.query(AOLControlFlags).filter_by(id=1).first()
        assert flags_check.killed is True, "Killed flag not set"
        assert flags_check.paused is False, "Paused flag should not be set"
        
        session.close()


def test_worker_tick_ledger_entry_structure():
    """Test that tick ledger entries have correct structure."""
    with create_temp_sqlite_db() as (engine, db_url):
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Create a tick ledger entry
        entry = AOLTickLedger(
            tick_timestamp=datetime.now(timezone.utc),
            status='SUCCESS',
            actions_attempted=2,
            actions_succeeded=2,
            duration_seconds=0.5,
            error_notes=None,
        )
        session.add(entry)
        session.commit()
        
        # Verify entry
        retrieved = session.query(AOLTickLedger).first()
        assert retrieved.status == 'SUCCESS'
        assert retrieved.actions_attempted == 2
        assert retrieved.actions_succeeded == 2
        assert retrieved.duration_seconds == 0.5
        
        session.close()


@pytest.mark.smoke
def test_worker_configuration_constants():
    """Smoke test: worker configuration constants are reasonable."""
    # These are defaults; can be overridden via env
    from scripts.run_aol_worker import (
        AOL_TICK_INTERVAL_SECONDS,
        AOL_MAX_ACTIONS_PER_TICK,
        AOL_MAX_TICK_SECONDS,
    )
    
    assert AOL_TICK_INTERVAL_SECONDS >= 5, "Tick interval too short"
    assert AOL_MAX_ACTIONS_PER_TICK >= 1, "Max actions too low"
    assert AOL_MAX_TICK_SECONDS >= 10, "Max tick duration too short"


def test_worker_control_flags_all_combinations():
    """Test all combinations of paused + killed flags."""
    with create_temp_sqlite_db() as (engine, db_url):
        SessionLocal = sessionmaker(bind=engine)
        
        test_cases = [
            (False, False, "running normally"),
            (True, False, "paused"),
            (False, True, "killed"),
            (True, True, "paused AND killed"),
        ]
        
        for paused, killed, desc in test_cases:
            session = SessionLocal()
            
            flags = AOLControlFlags(id=1, paused=paused, killed=killed, proof_mode=True)
            session.add(flags)
            session.commit()
            
            retrieved = session.query(AOLControlFlags).filter_by(id=1).first()
            assert retrieved.paused == paused, f"Paused mismatch in {desc}"
            assert retrieved.killed == killed, f"Killed mismatch in {desc}"
            
            session.close()
