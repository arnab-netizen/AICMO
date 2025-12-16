"""
Action Queue Manager - Enqueue, dequeue, retry, and dead-letter logic.

Status lifecycle:
PENDING (not_before_utc not reached)
  ↓
READY (available for processing)
  ↓
(execute action)
  ├→ SUCCESS (terminal)
  ├→ FAILED (terminal, no retry)
  └→ RETRY (if attempts < MAX_RETRIES, re-enqueue)
    ↓
  RETRY (attempts incremented)
    ↓
  (try again)
    ├→ SUCCESS (terminal)
    ├→ FAILED (terminal)
    └→ DLQ (if attempts >= MAX_RETRIES)
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from aicmo.orchestration.models import AOLAction, AOLExecutionLog


class ActionQueue:
    """
    Manages action queue with retry, DLQ, and idempotency.
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5
    
    @staticmethod
    def enqueue_action(
        session: Session,
        action_type: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        not_before: Optional[datetime] = None,
    ) -> AOLAction:
        """
        Enqueue a new action.
        
        Args:
            session: SQLAlchemy session
            action_type: e.g. "POST_SOCIAL"
            payload: Dict (will be JSON-serialized)
            idempotency_key: Unique key (UUID generated if None)
            not_before: Scheduled execution time (now if None)
        
        Returns:
            AOLAction record
        """
        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())
        
        payload_json = json.dumps(payload) if payload else None
        
        action = AOLAction(
            idempotency_key=idempotency_key,
            action_type=action_type,
            payload_json=payload_json,
            status="PENDING",
            not_before_utc=not_before,
            attempts=0,
        )
        session.add(action)
        session.commit()
        return action
    
    @staticmethod
    def dequeue_next(session: Session, max_actions: int = 3) -> List[AOLAction]:
        """
        Dequeue up to max_actions ready actions.
        
        Ready = status is "READY" or "PENDING" with not_before_utc <= now
        
        Args:
            session: SQLAlchemy session
            max_actions: Max actions to fetch per call
        
        Returns:
            List of AOLAction records
        """
        now = datetime.utcnow()
        
        # Find READY actions or PENDING actions with not_before <= now
        stmt = (
            select(AOLAction)
            .where(
                and_(
                    AOLAction.status.in_(["READY", "PENDING"]),
                    (AOLAction.not_before_utc.is_(None) | (AOLAction.not_before_utc <= now))
                )
            )
            .limit(max_actions)
        )
        
        actions = session.execute(stmt).scalars().all()
        return actions
    
    @staticmethod
    def mark_success(session: Session, action_id: int) -> None:
        """Mark action as successfully completed."""
        action = session.get(AOLAction, action_id)
        if action:
            action.status = "SUCCESS"
            session.commit()
    
    @staticmethod
    def mark_failed(session: Session, action_id: int, error_msg: str) -> None:
        """Mark action as failed (terminal)."""
        action = session.get(AOLAction, action_id)
        if action:
            action.status = "FAILED"
            action.last_error = error_msg
            session.commit()
    
    @staticmethod
    def mark_retry(session: Session, action_id: int, error_msg: str) -> None:
        """Mark action for retry (if attempts < MAX_RETRIES, else DLQ)."""
        action = session.get(AOLAction, action_id)
        if not action:
            return
        
        action.attempts += 1
        action.last_error = error_msg
        
        if action.attempts >= ActionQueue.MAX_RETRIES:
            action.status = "DLQ"
        else:
            action.status = "RETRY"
            action.not_before_utc = datetime.utcnow() + timedelta(seconds=ActionQueue.RETRY_DELAY_SECONDS)
        
        session.commit()
    
    @staticmethod
    def log_execution(
        session: Session,
        action_id: int,
        level: str,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        message: str,
        artifact_ref: Optional[str] = None,
        artifact_sha256: Optional[str] = None,
    ) -> None:
        """Log an execution event for an action."""
        log = AOLExecutionLog(
            action_id=action_id,
            ts_utc=datetime.utcnow(),
            level=level,
            message=message,
            artifact_ref=artifact_ref,
            artifact_sha256=artifact_sha256,
        )
        session.add(log)
        session.commit()
