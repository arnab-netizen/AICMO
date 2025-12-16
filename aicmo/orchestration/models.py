"""
Autonomy Orchestration Layer (AOL) Database Models.

5 core tables:
1. aol_control_flags - Global daemon control (pause, kill, proof mode)
2. aol_tick_ledger - Per-tick execution summaries
3. aol_lease - Distributed lock for daemon exclusivity
4. aol_actions - Task queue (PENDING → SUCCESS/FAILED/DLQ)
5. aol_execution_logs - Detailed action execution traces

NO interpretation allowed. Exact ORM definition only.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Float, LargeBinary,
    UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base

# Use a separate Base for AOL to avoid foreign key conflicts with other models
Base = declarative_base()


class AOLControlFlags(Base):
    """Global daemon control state.
    
    Single row (or very few) controlling daemon behavior.
    - paused: True = daemon stops processing (holds lease, waits)
    - killed: True = daemon must exit immediately
    - proof_mode: True = all actions write artifacts only, no real execution
    - updated_at_utc: Last flag modification timestamp
    """
    __tablename__ = "aol_control_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paused = Column(Boolean, default=False, nullable=False)
    killed = Column(Boolean, default=False, nullable=False)
    proof_mode = Column(Boolean, default=False, nullable=False)
    updated_at_utc = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "paused": self.paused,
            "killed": self.killed,
            "proof_mode": self.proof_mode,
            "updated_at_utc": self.updated_at_utc.isoformat() if self.updated_at_utc else None,
        }


class AOLTickLedger(Base):
    """Per-tick execution summary.
    
    One row per daemon tick (loop iteration).
    - status: SUCCESS (all actions processed), PARTIAL (some failed), FAIL (critical error)
    - actions_attempted: Number of actions processed in this tick
    - actions_succeeded: Number that reached terminal SUCCESS state
    - notes: Tick-level error/diagnostic info
    """
    __tablename__ = "aol_tick_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at_utc = Column(DateTime, nullable=False)
    finished_at_utc = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # SUCCESS, PARTIAL, FAIL
    notes = Column(Text, nullable=True)
    actions_attempted = Column(Integer, default=0, nullable=False)
    actions_succeeded = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_aol_tick_ledger_started_at", "started_at_utc"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "started_at_utc": self.started_at_utc.isoformat() if self.started_at_utc else None,
            "finished_at_utc": self.finished_at_utc.isoformat() if self.finished_at_utc else None,
            "status": self.status,
            "notes": self.notes,
            "actions_attempted": self.actions_attempted,
            "actions_succeeded": self.actions_succeeded,
        }


class AOLLease(Base):
    """Distributed lock for daemon exclusivity.
    
    Ensures only one daemon instance runs at a time.
    - owner: Daemon identifier (hostname:pid or similar)
    - acquired_at_utc: Lock acquisition time
    - renewed_at_utc: Last heartbeat/renewal time
    - expires_at_utc: Absolute lease expiration (safety timeout)
    
    Atomic acquire: INSERT if not exists, or UPDATE if owner=self and expired=False
    """
    __tablename__ = "aol_lease"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(String(255), nullable=False, unique=True)
    acquired_at_utc = Column(DateTime, nullable=False)
    renewed_at_utc = Column(DateTime, nullable=False)
    expires_at_utc = Column(DateTime, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "owner": self.owner,
            "acquired_at_utc": self.acquired_at_utc.isoformat() if self.acquired_at_utc else None,
            "renewed_at_utc": self.renewed_at_utc.isoformat() if self.renewed_at_utc else None,
            "expires_at_utc": self.expires_at_utc.isoformat() if self.expires_at_utc else None,
        }


class AOLAction(Base):
    """Task queue entry.
    
    Status flow:
    - PENDING: Awaiting execution (not_before_utc not reached)
    - READY: Available for immediate execution
    - RETRY: Failed, eligible for retry (attempts < MAX_RETRIES)
    - DLQ: Dead Letter Queue (max retries exhausted)
    - SUCCESS: Completed successfully
    - FAILED: Terminal failure (no retry)
    - CANCELLED: Explicitly cancelled
    
    Fields:
    - idempotency_key: UNIQUE - prevents duplicate execution
    - action_type: e.g. "POST_SOCIAL", "FETCH_LEADS", "SEND_EMAIL"
    - payload_json: Action-specific JSON data
    - status: Current state
    - not_before_utc: Scheduled execution time (NULL = execute now)
    - attempts: Retry counter
    - last_error: Most recent error message
    - created_at_utc: Action creation time
    """
    __tablename__ = "aol_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    action_type = Column(String(100), nullable=False)
    payload_json = Column(Text, nullable=True)  # JSON string
    status = Column(String(20), nullable=False)  # PENDING, READY, RETRY, DLQ, SUCCESS, FAILED, CANCELLED
    not_before_utc = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    created_at_utc = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_aol_actions_status", "status"),
        Index("idx_aol_actions_not_before", "not_before_utc"),
        Index("idx_aol_actions_idempotency", "idempotency_key"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "idempotency_key": self.idempotency_key,
            "action_type": self.action_type,
            "payload_json": self.payload_json,
            "status": self.status,
            "not_before_utc": self.not_before_utc.isoformat() if self.not_before_utc else None,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "created_at_utc": self.created_at_utc.isoformat() if self.created_at_utc else None,
        }


class AOLExecutionLog(Base):
    """Detailed action execution trace.
    
    One or more rows per action, recording every step, error, and artifact.
    - action_id: FK to aol_actions.id
    - ts_utc: Log entry timestamp
    - level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - message: Log message (human-readable)
    - artifact_ref: Path or URI to artifact (e.g., file path, S3 URL)
    - artifact_sha256: SHA256 hash of artifact content (for integrity verification)
    """
    __tablename__ = "aol_execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(Integer, nullable=False)  # FK to aol_actions.id (soft FK for safety)
    ts_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String(20), nullable=False)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=True)
    artifact_ref = Column(Text, nullable=True)  # Path or URI
    artifact_sha256 = Column(String(64), nullable=True)  # Hex string

    __table_args__ = (
        Index("idx_aol_execution_logs_action_id", "action_id"),
        Index("idx_aol_execution_logs_ts_utc", "ts_utc"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "ts_utc": self.ts_utc.isoformat() if self.ts_utc else None,
            "level": self.level,
            "message": self.message,
            "artifact_ref": self.artifact_ref,
            "artifact_sha256": self.artifact_sha256,
        }
