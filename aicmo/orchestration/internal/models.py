"""
Orchestration module database models.

Contains persistent storage for saga/workflow orchestration:
- WorkflowRunDB: Workflow execution tracking and compensation scoping

Phase 4 Lane C: DB-backed saga compensation with HARD DELETE semantics.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, Index

from aicmo.core.db import Base


class WorkflowRunDB(Base):
    """
    Persistent storage for workflow execution runs.
    
    Purpose:
    1. **Compensation Scope**: Provides workflow_run_id for DELETE operations
    2. **Idempotency**: Prevents duplicate workflow execution on retries
    3. **Concurrency Control**: Ensures only one worker processes a run
    4. **Status Tracking**: Records workflow lifecycle (RUNNING, COMPLETED, FAILED, COMPENSATED)
    
    Lifecycle:
    - RUNNING: Workflow executing forward steps
    - COMPLETED: All steps succeeded, package created
    - FAILED: Step failed, compensation not yet triggered
    - COMPENSATING: Compensation in progress
    - COMPENSATED: Compensation complete, all orphan rows deleted
    
    Concurrency Pattern (optimistic locking via atomic UPDATE):
    ```sql
    UPDATE workflow_runs 
    SET claimed_by = :worker_id, claimed_at = NOW(), lease_expires_at = NOW() + INTERVAL '5 minutes'
    WHERE id = :run_id AND (claimed_by IS NULL OR lease_expires_at < NOW())
    RETURNING id
    ```
    
    Idempotency Key: (brief_id, created_at) - One run per brief per timestamp window
    Compensation Scope: All DELETE operations use workflow_run_id WHERE clauses
    """
    
    __tablename__ = "workflow_runs"
    
    # Primary key (used as compensation scope identifier)
    id = Column(String, primary_key=True)  # workflow_run_id (UUID as string)
    
    # Workflow inputs
    brief_id = Column(String, nullable=False, index=True)  # Logical FK to onboarding_brief
    
    # Status tracking
    status = Column(
        String,
        nullable=False,
        index=True,
        default="RUNNING",
    )  # RUNNING, COMPLETED, FAILED, COMPENSATING, COMPENSATED
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Concurrency control (lease-based locking)
    claimed_by = Column(String, nullable=True)  # worker_id (hostname + PID)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    lease_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional context (JSON for flexibility)
    # Use 'meta' as column name to avoid SQLAlchemy reserved word 'metadata'
    meta = Column("metadata", JSON, nullable=False, default=dict)  # step_ids, error_context, etc.


# Composite index for concurrency queries (find expired leases)
Index(
    "ix_workflow_runs_status_claimed_expires",
    WorkflowRunDB.status,
    WorkflowRunDB.claimed_by,
    WorkflowRunDB.lease_expires_at,
)
