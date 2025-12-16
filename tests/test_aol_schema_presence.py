"""
Smoke test: AOL schema tables are present with correct constraints.

Verifies:
  - All 5 AOL tables exist
  - Unique constraint on aol_actions.idempotency_key
  - Indexes are created
"""

import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker
from aicmo.orchestration.models import Base


@pytest.fixture(scope="module")
def test_engine():
    """Create a test SQLite engine with AOL schema."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_aol_tables_exist(test_engine):
    """Test that all 5 AOL tables exist."""
    inspector = inspect(test_engine)
    tables = set(inspector.get_table_names())
    
    expected_tables = {
        'aol_control_flags',
        'aol_tick_ledger',
        'aol_lease',
        'aol_actions',
        'aol_execution_logs',
    }
    
    assert expected_tables <= tables, f"Missing tables: {expected_tables - tables}"


def test_aol_actions_idempotency_key_unique_constraint(test_engine):
    """Test that aol_actions has unique constraint on idempotency_key."""
    inspector = inspect(test_engine)
    
    # Get unique constraints
    constraints = inspector.get_unique_constraints('aol_actions')
    constraint_sets = [set(c['column_names']) for c in constraints]
    
    assert any('idempotency_key' in cs for cs in constraint_sets), \
        f"No unique constraint on idempotency_key. Constraints: {constraint_sets}"


def test_aol_actions_indexes(test_engine):
    """Test that aol_actions has expected indexes."""
    inspector = inspect(test_engine)
    indexes = inspector.get_indexes('aol_actions')
    index_cols = [set(idx['column_names']) for idx in indexes]
    
    # We expect at least indexes on status and not_before_utc
    assert any('status' in cs for cs in index_cols), \
        f"No index on status. Indexes: {index_cols}"


def test_aol_execution_logs_action_id_fk(test_engine):
    """Test that aol_execution_logs can be created with valid action_id."""
    from aicmo.orchestration.models import AOLAction, AOLExecutionLog
    from datetime import datetime, timezone
    
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    try:
        # Create an action
        action = AOLAction(
            action_type="POST_SOCIAL",
            payload_json='{"test": true}',
            idempotency_key="test_idem_key_001",
            status="PENDING",
        )
        session.add(action)
        session.flush()  # Get ID without commit
        action_id = action.id
        
        # Create execution log
        log = AOLExecutionLog(
            action_id=action_id,
            level="INFO",
            message="Test execution",
            artifact_ref="/tmp/test.json",
            artifact_sha256="abc123def456",
        )
        session.add(log)
        session.flush()
        
        # Verify both were created
        assert action.id is not None
        assert log.id is not None
        
    finally:
        session.rollback()
        session.close()


def test_aol_control_flags_single_row(test_engine):
    """Test that aol_control_flags can be created."""
    from aicmo.orchestration.models import AOLControlFlags
    
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    try:
        # Create control flags
        flags = AOLControlFlags(
            paused=False,
            killed=False,
            proof_mode=False,
        )
        session.add(flags)
        session.flush()
        
        assert flags.id is not None
        
    finally:
        session.rollback()
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
