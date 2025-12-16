"""
Orchestrator repositories.

Provides data access for:
- Unsubscribe list
- Suppression list
- Orchestrator run state (lease management)
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from aicmo.cam.orchestrator.models import (
    UnsubscribeDB,
    SuppressionDB,
    OrchestratorRunDB,
    RunStatus,
)


class UnsubscribeRepository:
    """Repository for unsubscribe list."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def is_unsubscribed(self, email: str) -> bool:
        """Check if email is on unsubscribe list."""
        if not email:
            return False
        
        count = (
            self.session.query(UnsubscribeDB)
            .filter(UnsubscribeDB.email == email.lower())
            .count()
        )
        return count > 0
    
    def add_unsubscribe(
        self,
        email: str,
        reason: Optional[str] = None,
        campaign_id: Optional[int] = None,
    ) -> UnsubscribeDB:
        """Add email to unsubscribe list (idempotent)."""
        existing = (
            self.session.query(UnsubscribeDB)
            .filter(UnsubscribeDB.email == email.lower())
            .first()
        )
        
        if existing:
            return existing
        
        unsub = UnsubscribeDB(
            email=email.lower(),
            reason=reason or "user_request",
            campaign_id=campaign_id,
        )
        self.session.add(unsub)
        self.session.flush()
        return unsub


class SuppressionRepository:
    """Repository for suppression list."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def is_suppressed(
        self,
        email: Optional[str] = None,
        domain: Optional[str] = None,
        identity_hash: Optional[str] = None,
    ) -> bool:
        """
        Check if email/domain/identity_hash is suppressed.
        
        Returns True if ANY of the provided identifiers match an active suppression.
        """
        if not any([email, domain, identity_hash]):
            return False
        
        conditions = []
        
        if email:
            conditions.append(SuppressionDB.email == email.lower())
            # Also check domain suppression
            if '@' in email:
                email_domain = email.split('@')[1].lower()
                conditions.append(SuppressionDB.domain == email_domain)
        
        if domain:
            conditions.append(SuppressionDB.domain == domain.lower())
        
        if identity_hash:
            conditions.append(SuppressionDB.identity_hash == identity_hash)
        
        count = (
            self.session.query(SuppressionDB)
            .filter(
                and_(
                    SuppressionDB.active == True,
                    or_(*conditions)
                )
            )
            .count()
        )
        
        return count > 0
    
    def add_suppression(
        self,
        reason: str,
        email: Optional[str] = None,
        domain: Optional[str] = None,
        identity_hash: Optional[str] = None,
    ) -> SuppressionDB:
        """Add entry to suppression list."""
        if not any([email, domain, identity_hash]):
            raise ValueError("Must provide at least one of: email, domain, identity_hash")
        
        suppression = SuppressionDB(
            email=email.lower() if email else None,
            domain=domain.lower() if domain else None,
            identity_hash=identity_hash,
            reason=reason,
            active=True,
        )
        self.session.add(suppression)
        self.session.flush()
        return suppression


class OrchestratorRunRepository:
    """Repository for orchestrator run state with lease management."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def try_claim_campaign(
        self,
        campaign_id: int,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
    ) -> Optional[OrchestratorRunDB]:
        """
        Attempt to claim campaign for processing (atomic).
        
        Returns run if claimed, None if already claimed by another worker.
        Uses database-level atomic UPDATE to prevent race conditions.
        """
        lease_expires_at = now + lease_duration
        
        # Try to find an existing run that's either:
        # 1. Unclaimed (no active runs)
        # 2. Expired lease
        existing = (
            self.session.query(OrchestratorRunDB)
            .filter(
                and_(
                    OrchestratorRunDB.campaign_id == campaign_id,
                    OrchestratorRunDB.status.in_([RunStatus.CLAIMED.value, RunStatus.RUNNING.value]),
                    OrchestratorRunDB.lease_expires_at >= now,
                )
            )
            .first()
        )
        
        if existing:
            # Campaign already claimed by active worker
            return None
        
        # No active run, create new one
        run = OrchestratorRunDB(
            campaign_id=campaign_id,
            status=RunStatus.CLAIMED.value,
            claimed_by=worker_id,
            lease_expires_at=lease_expires_at,
            heartbeat_at=now,
        )
        self.session.add(run)
        self.session.flush()
        return run
    
    def refresh_lease(
        self,
        run_id: str,
        lease_duration: timedelta,
        now: datetime,
    ) -> None:
        """Refresh lease expiration (heartbeat)."""
        run = self.session.query(OrchestratorRunDB).filter_by(id=run_id).first()
        if run:
            run.lease_expires_at = now + lease_duration
            run.heartbeat_at = now
            self.session.flush()
    
    def update_progress(
        self,
        run_id: str,
        leads_processed: int = 0,
        jobs_created: int = 0,
        attempts_succeeded: int = 0,
        attempts_failed: int = 0,
    ) -> None:
        """Update run progress counters."""
        run = self.session.query(OrchestratorRunDB).filter_by(id=run_id).first()
        if run:
            run.leads_processed += leads_processed
            run.jobs_created += jobs_created
            run.attempts_succeeded += attempts_succeeded
            run.attempts_failed += attempts_failed
            self.session.flush()
    
    def mark_completed(
        self,
        run_id: str,
        now: datetime,
        status: RunStatus = RunStatus.COMPLETED,
        error: Optional[str] = None,
    ) -> None:
        """Mark run as completed/stopped/failed."""
        run = self.session.query(OrchestratorRunDB).filter_by(id=run_id).first()
        if run:
            run.status = status.value
            run.completed_at = now
            if error:
                run.last_error = error
            self.session.flush()
