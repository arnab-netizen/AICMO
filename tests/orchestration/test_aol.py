"""Tests for Autonomy Orchestration Layer."""

import json
import os
import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from aicmo.orchestration.models import (
    Base, AOLControlFlags, AOLTickLedger, AOLLease, AOLAction, AOLExecutionLog
)
from aicmo.orchestration.daemon import AOLDaemon
from aicmo.orchestration.queue import ActionQueue
from aicmo.orchestration.lease import LeaseManager
from aicmo.orchestration.adapters.social_adapter import handle_post_social, RealRunUnconfigured


@pytest.fixture
def test_db_path():
    """Create temporary SQLite database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db(test_db_path):
    """Create in-memory SQLite database for testing."""
    engine = create_engine(f"sqlite:///{test_db_path}", future=True)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(test_db):
    """Create SQLAlchemy session."""
    Session = sessionmaker(bind=test_db)
    sess = Session()
    yield sess
    sess.close()


class TestAOLModels:
    """Test AOL database models."""
    
    def test_control_flags_creation(self, session):
        """Test AOL control flags creation."""
        flags = AOLControlFlags(
            paused=False,
            killed=False,
            proof_mode=True,
        )
        session.add(flags)
        session.commit()
        
        retrieved = session.query(AOLControlFlags).first()
        assert retrieved is not None
        assert retrieved.proof_mode is True
        assert retrieved.paused is False
    
    def test_tick_ledger_creation(self, session):
        """Test tick ledger record creation."""
        tick = AOLTickLedger(
            started_at_utc=datetime.utcnow(),
            finished_at_utc=datetime.utcnow(),
            status="SUCCESS",
            notes="Test tick",
            actions_attempted=0,
            actions_succeeded=0,
        )
        session.add(tick)
        session.commit()
        
        retrieved = session.query(AOLTickLedger).first()
        assert retrieved is not None
        assert retrieved.status == "SUCCESS"
    
    def test_lease_creation(self, session):
        """Test lease record creation."""
        now = datetime.utcnow()
        lease = AOLLease(
            owner="test:1234",
            acquired_at_utc=now,
            renewed_at_utc=now,
            expires_at_utc=now,
        )
        session.add(lease)
        session.commit()
        
        retrieved = session.query(AOLLease).first()
        assert retrieved is not None
        assert retrieved.owner == "test:1234"
    
    def test_action_creation(self, session):
        """Test action record creation."""
        action = AOLAction(
            idempotency_key="test-key-001",
            action_type="POST_SOCIAL",
            payload_json=json.dumps({"platform": "twitter"}),
            status="PENDING",
        )
        session.add(action)
        session.commit()
        
        retrieved = session.query(AOLAction).filter_by(
            idempotency_key="test-key-001"
        ).first()
        assert retrieved is not None
        assert retrieved.action_type == "POST_SOCIAL"
    
    def test_execution_log_creation(self, session):
        """Test execution log creation."""
        log = AOLExecutionLog(
            action_id=1,
            ts_utc=datetime.utcnow(),
            level="INFO",
            message="Test log entry",
        )
        session.add(log)
        session.commit()
        
        retrieved = session.query(AOLExecutionLog).first()
        assert retrieved is not None
        assert retrieved.level == "INFO"


class TestActionQueue:
    """Test action queue operations."""
    
    def test_enqueue_action(self, session):
        """Test enqueueing an action."""
        action = ActionQueue.enqueue_action(
            session,
            action_type="POST_SOCIAL",
            payload={"platform": "twitter", "content": "Hello"},
            idempotency_key="test-123",
        )
        
        assert action.id is not None
        assert action.status == "PENDING"
        assert action.idempotency_key == "test-123"
    
    def test_dequeue_ready_action(self, session):
        """Test dequeueing ready actions."""
        # Enqueue
        ActionQueue.enqueue_action(
            session,
            action_type="POST_SOCIAL",
            payload={"platform": "twitter"},
        )
        
        # Dequeue
        actions = ActionQueue.dequeue_next(session, max_actions=1)
        assert len(actions) == 1
        assert actions[0].status == "PENDING"
    
    def test_mark_success(self, session):
        """Test marking action as success."""
        action = ActionQueue.enqueue_action(
            session,
            action_type="TEST",
            payload={},
        )
        
        ActionQueue.mark_success(session, action.id)
        
        updated = session.get(AOLAction, action.id)
        assert updated.status == "SUCCESS"
    
    def test_mark_failed(self, session):
        """Test marking action as failed."""
        action = ActionQueue.enqueue_action(
            session,
            action_type="TEST",
            payload={},
        )
        
        ActionQueue.mark_failed(session, action.id, "Test error")
        
        updated = session.get(AOLAction, action.id)
        assert updated.status == "FAILED"
        assert updated.last_error == "Test error"
    
    def test_mark_retry(self, session):
        """Test marking action for retry."""
        action = ActionQueue.enqueue_action(
            session,
            action_type="TEST",
            payload={},
        )
        
        ActionQueue.mark_retry(session, action.id, "Temporary error")
        
        updated = session.get(AOLAction, action.id)
        assert updated.status == "RETRY"
        assert updated.attempts == 1
    
    def test_retry_exhaustion(self, session):
        """Test that action goes to DLQ after max retries."""
        action = ActionQueue.enqueue_action(
            session,
            action_type="TEST",
            payload={},
        )
        
        # Retry MAX_RETRIES times
        for _ in range(ActionQueue.MAX_RETRIES):
            ActionQueue.mark_retry(session, action.id, "Error")
        
        updated = session.get(AOLAction, action.id)
        assert updated.status == "DLQ"


class TestLeaseManager:
    """Test distributed lease management."""
    
    def test_acquire_lease_first_time(self, test_db_path):
        """Test first-time lease acquisition."""
        db_url = f"sqlite:///{test_db_path}"
        
        # Create tables
        engine = create_engine(db_url, future=True)
        Base.metadata.create_all(engine)
        
        manager = LeaseManager(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        success, msg = manager.acquire_or_renew(session)
        
        assert success is True
        assert "Lease acquired" in msg
        
        session.close()
        engine.dispose()
    
    def test_renew_same_owner(self, test_db_path):
        """Test lease renewal by same owner."""
        db_url = f"sqlite:///{test_db_path}"
        
        # Create tables
        engine = create_engine(db_url, future=True)
        Base.metadata.create_all(engine)
        
        manager = LeaseManager(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # First acquire
        success1, _ = manager.acquire_or_renew(session)
        assert success1 is True
        
        # Renew
        success2, msg = manager.acquire_or_renew(session)
        assert success2 is True
        assert "renewed" in msg.lower()
        
        session.close()
        engine.dispose()


class TestSocialAdapter:
    """Test POST_SOCIAL action adapter."""
    
    def test_proof_mode_post_social(self, session, tmp_path):
        """Test POST_SOCIAL in PROOF mode."""
        # Override artifacts directory for test
        import aicmo.orchestration.adapters.social_adapter
        original_path = aicmo.orchestration.adapters.social_adapter.Path
        
        action = AOLAction(
            id=1,
            idempotency_key="test-post-001",
            action_type="POST_SOCIAL",
            payload_json=json.dumps({
                "social_platform": "twitter",
                "content": "Test post",
                "audience": "followers"
            }),
            status="PENDING",
        )
        session.add(action)
        session.commit()
        
        # Execute in PROOF mode
        payload = json.loads(action.payload_json)
        payload["idempotency_key"] = action.idempotency_key
        
        # This should not raise in PROOF mode
        handle_post_social(session, action.id, payload, proof_mode=True)
        
        updated = session.get(AOLAction, action.id)
        assert updated.status == "SUCCESS"
    
    def test_real_mode_post_social_fails(self, session):
        """Test POST_SOCIAL in REAL mode raises error."""
        action = AOLAction(
            id=2,
            idempotency_key="test-post-002",
            action_type="POST_SOCIAL",
            payload_json=json.dumps({
                "social_platform": "twitter",
                "content": "Test post",
                "audience": "followers"
            }),
            status="PENDING",
        )
        session.add(action)
        session.commit()
        
        payload = json.loads(action.payload_json)
        payload["idempotency_key"] = action.idempotency_key
        
        # This should raise RealRunUnconfigured
        with pytest.raises(RealRunUnconfigured):
            handle_post_social(session, action.id, payload, proof_mode=False)
        
        updated = session.get(AOLAction, action.id)
        assert updated.status == "FAILED"


class TestAOLDaemon:
    """Test daemon loop."""
    
    def test_daemon_runs_ticks(self, test_db_path):
        """Test daemon runs multiple ticks."""
        db_url = f"sqlite:///{test_db_path}"
        
        # Create engine and tables
        engine = create_engine(db_url, future=True)
        Base.metadata.create_all(engine)
        engine.dispose()
        
        daemon = AOLDaemon(db_url)
        
        # Run 2 ticks
        exit_code = daemon.run(max_ticks=2)
        
        assert exit_code == 0
    
    def test_daemon_respects_pause_flag(self, test_db):
        """Test daemon respects pause flag."""
        # This would require more complex setup
        # Skipping for now as it requires async behavior
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
