"""
Repository for workflow run persistence operations.

Provides safe database operations for workflow execution tracking,
compensation scoping, and concurrency control.

Phase 4 Lane C: DB-backed saga compensation with HARD DELETE semantics.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import text

from aicmo.orchestration.internal.models import WorkflowRunDB
from aicmo.shared.ids import BriefId


class WorkflowRunRepository:
    """
    Repository for workflow run database operations.
    
    Responsibilities:
    1. Create workflow runs with unique workflow_run_id
    2. Query run status for idempotency checks
    3. Claim runs for exclusive worker execution (concurrency control)
    4. Update run status through lifecycle transitions
    5. Support compensation scoping queries
    """
    
    def __init__(self, session: Session):
        self._session = session
    
    def create_run(
        self,
        brief_id: BriefId,
        workflow_run_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> WorkflowRunDB:
        """
        Create a new workflow run record.
        
        Args:
            brief_id: Brief ID for this workflow execution
            workflow_run_id: Optional explicit ID (default: generated UUID)
            metadata: Optional additional context
        
        Returns:
            Newly created WorkflowRunDB
        
        Raises:
            IntegrityError: If workflow_run_id already exists (idempotency violation)
        """
        run_id = workflow_run_id or str(uuid4())
        
        run = WorkflowRunDB(
            id=run_id,
            brief_id=str(brief_id),
            status="RUNNING",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            meta=metadata or {},
            retry_count=0,
        )
        
        self._session.add(run)
        self._session.flush()  # Flush to detect uniqueness violations immediately
        
        return run
    
    def get_run(self, workflow_run_id: str) -> Optional[WorkflowRunDB]:
        """
        Retrieve workflow run by ID.
        
        Args:
            workflow_run_id: Unique workflow run identifier
        
        Returns:
            WorkflowRunDB if found, None otherwise
        """
        return self._session.query(WorkflowRunDB).filter(
            WorkflowRunDB.id == workflow_run_id
        ).first()
    
    def get_runs_by_brief(self, brief_id: BriefId) -> list[WorkflowRunDB]:
        """
        Get all workflow runs for a specific brief.
        
        Useful for debugging and idempotency analysis.
        
        Args:
            brief_id: Brief identifier
        
        Returns:
            List of WorkflowRunDB ordered by created_at DESC
        """
        return (
            self._session.query(WorkflowRunDB)
            .filter(WorkflowRunDB.brief_id == str(brief_id))
            .order_by(WorkflowRunDB.created_at.desc())
            .all()
        )
    
    def claim_run(
        self,
        workflow_run_id: str,
        worker_id: str,
        lease_duration_seconds: int = 300,
    ) -> bool:
        """
        Atomically claim a workflow run for exclusive execution.
        
        Uses optimistic locking via UPDATE...WHERE to prevent double execution.
        
        Args:
            workflow_run_id: Run to claim
            worker_id: Identifier for this worker (e.g., "worker-abc123")
            lease_duration_seconds: Lease expiration (default: 5 minutes)
        
        Returns:
            True if claim succeeded, False if already claimed or not found
        """
        now = datetime.now(timezone.utc)
        lease_expires = now + timedelta(seconds=lease_duration_seconds)
        
        # Atomic claim: update only if unclaimed or lease expired
        result = self._session.execute(
            text("""
                UPDATE workflow_runs
                SET claimed_by = :worker_id,
                    claimed_at = :now,
                    lease_expires_at = :lease_expires,
                    updated_at = :now
                WHERE id = :run_id
                  AND (claimed_by IS NULL OR lease_expires_at < :now)
                RETURNING id
            """),
            {
                "run_id": workflow_run_id,
                "worker_id": worker_id,
                "now": now,
                "lease_expires": lease_expires,
            },
        )
        
        # If UPDATE returned a row, claim succeeded
        row = result.fetchone()
        return row is not None
    
    def update_status(
        self,
        workflow_run_id: str,
        status: str,
        error: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """
        Update workflow run status.
        
        Args:
            workflow_run_id: Run to update
            status: New status (RUNNING, COMPLETED, FAILED, COMPENSATING, COMPENSATED)
            error: Optional error message if status=FAILED
            completed_at: Optional completion timestamp
        """
        run = self.get_run(workflow_run_id)
        if not run:
            raise ValueError(f"Workflow run {workflow_run_id} not found")
        
        run.status = status
        run.updated_at = datetime.now(timezone.utc)
        
        if error:
            run.last_error = error
        
        if completed_at:
            run.completed_at = completed_at
        
        self._session.flush()
    
    def increment_retry_count(self, workflow_run_id: str) -> None:
        """
        Increment retry count for a workflow run.
        
        Args:
            workflow_run_id: Run to update
        """
        run = self.get_run(workflow_run_id)
        if not run:
            raise ValueError(f"Workflow run {workflow_run_id} not found")
        
        run.retry_count += 1
        run.updated_at = datetime.now(timezone.utc)
        self._session.flush()
    
    def release_claim(self, workflow_run_id: str) -> None:
        """
        Release claim on a workflow run (for graceful shutdown).
        
        Args:
            workflow_run_id: Run to release
        """
        run = self.get_run(workflow_run_id)
        if not run:
            return
        
        run.claimed_by = None
        run.claimed_at = None
        run.lease_expires_at = None
        run.updated_at = datetime.now(timezone.utc)
        self._session.flush()
