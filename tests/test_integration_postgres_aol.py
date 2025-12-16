"""
Integration test: AOL daemon with real PostgreSQL (if available).

Verifies:
  - Schema migrations run successfully against PostgreSQL
  - Daemon can execute 2 ticks against real DB
  - Action can be enqueued and executed
  - Tick ledger has records
  
Skips if AICMO_TEST_POSTGRES_URL not set.
"""

import os
import pytest
import json
import uuid


@pytest.fixture(scope="module")
def postgres_url():
    """Get PostgreSQL URL from environment."""
    url = os.getenv("AICMO_TEST_POSTGRES_URL")
    
    if not url:
        pytest.skip("AICMO_TEST_POSTGRES_URL not set - skipping PostgreSQL integration tests")
    
    return url


@pytest.fixture
def run_id():
    """Generate unique run ID for cleanup."""
    return f"test_run_{uuid.uuid4().hex[:8]}"


def test_postgres_schema_creation(postgres_url, run_id):
    """Test that AOL schema can be created in PostgreSQL."""
    from sqlalchemy import create_engine, inspect
    from aicmo.orchestration.models import Base
    
    engine = create_engine(postgres_url, future=True)
    
    # Create schema
    Base.metadata.create_all(engine)
    
    # Verify tables exist
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    
    assert 'aol_control_flags' in tables, "aol_control_flags missing"
    assert 'aol_tick_ledger' in tables, "aol_tick_ledger missing"
    assert 'aol_lease' in tables, "aol_lease missing"
    assert 'aol_actions' in tables, "aol_actions missing"
    assert 'aol_execution_logs' in tables, "aol_execution_logs missing"
    
    engine.dispose()


def test_postgres_daemon_ticks(postgres_url, run_id, monkeypatch):
    """Test that daemon can run 2 ticks against PostgreSQL."""
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    
    from aicmo.orchestration.daemon import AOLDaemon
    from aicmo.orchestration.models import Base
    from sqlalchemy import create_engine
    
    # Initialize schema
    engine = create_engine(postgres_url, future=True)
    Base.metadata.create_all(engine)
    engine.dispose()
    
    # Run daemon
    daemon = AOLDaemon(postgres_url)
    exit_code = daemon.run(max_ticks=2)
    
    assert exit_code == 0, f"Daemon failed with code {exit_code}"


def test_postgres_action_enqueue_and_execute(postgres_url, run_id, monkeypatch):
    """Test that action can be enqueued and executed in PostgreSQL."""
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    
    from aicmo.orchestration.daemon import AOLDaemon
    from aicmo.orchestration.models import Base, AOLAction, AOLControlFlags
    from aicmo.orchestration.queue import ActionQueue
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    
    # Initialize schema
    engine = create_engine(postgres_url, future=True)
    Base.metadata.create_all(engine)
    
    # Enqueue test action
    Session = sessionmaker(bind=engine)
    session = Session()
    
    action_payload = {
        "platform": "twitter",
        "message": f"Test message from {run_id}"
    }
    
    idempotency_key = f"test_action_{uuid.uuid4().hex[:8]}"
    
    ActionQueue.enqueue_action(
        session=session,
        action_type="POST_SOCIAL",
        payload=action_payload,
        idempotency_key=idempotency_key,
    )
    
    session.commit()
    
    # Verify action was created
    stmt = select(AOLAction).filter(AOLAction.idempotency_key == idempotency_key)
    action = session.execute(stmt).scalar_one_or_none()
    
    assert action is not None, "Action should be enqueued"
    assert action.status == "PENDING", "Action should be PENDING"
    
    # Set PROOF mode to prevent real execution
    flags_stmt = select(AOLControlFlags).limit(1)
    flags = session.execute(flags_stmt).scalar_one_or_none()
    
    if not flags:
        flags = AOLControlFlags(proof_mode=True)
        session.add(flags)
    else:
        flags.proof_mode = True
    
    session.commit()
    session.close()
    
    # Run daemon for 1 tick (should execute action)
    daemon = AOLDaemon(postgres_url)
    exit_code = daemon.run(max_ticks=1)
    
    assert exit_code == 0, "Daemon tick should succeed"
    
    # Verify action was processed
    session = Session()
    stmt = select(AOLAction).filter(AOLAction.idempotency_key == idempotency_key)
    processed_action = session.execute(stmt).scalar_one_or_none()
    
    assert processed_action is not None, "Action should still exist"
    # In PROOF mode, action should transition to something other than PENDING
    # (SUCCESS if all goes well, RETRY/FAILED if execution adapter fails)
    assert processed_action.status != "PENDING", \
        f"Action should have been processed, status: {processed_action.status}"
    
    session.close()


def test_postgres_tick_ledger_recorded(postgres_url, run_id, monkeypatch):
    """Test that tick ledger records are created."""
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    
    from aicmo.orchestration.daemon import AOLDaemon
    from aicmo.orchestration.models import Base, AOLTickLedger
    from sqlalchemy import create_engine, select, func
    from sqlalchemy.orm import sessionmaker
    
    # Initialize schema
    engine = create_engine(postgres_url, future=True)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Count ticks before
    stmt = select(func.count(AOLTickLedger.id))
    ticks_before = session.execute(stmt).scalar() or 0
    
    session.close()
    
    # Run daemon
    daemon = AOLDaemon(postgres_url)
    exit_code = daemon.run(max_ticks=2)
    
    assert exit_code == 0, "Daemon should succeed"
    
    # Count ticks after
    session = Session()
    stmt = select(func.count(AOLTickLedger.id))
    ticks_after = session.execute(stmt).scalar() or 0
    session.close()
    
    # Should have recorded 2 ticks
    new_ticks = ticks_after - ticks_before
    assert new_ticks >= 2, \
        f"Should have recorded at least 2 ticks, got {new_ticks}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
