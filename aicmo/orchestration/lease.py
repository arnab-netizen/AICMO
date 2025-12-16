"""
Distributed Lease Manager - Ensures only one daemon runs at a time.

Atomic acquire: Try to claim or renew lease. Fail safely if another daemon holds it.
"""

import os
import socket
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session, sessionmaker

from aicmo.orchestration.models import AOLLease


def get_daemon_owner() -> str:
    """Generate unique daemon owner identifier: hostname:pid"""
    hostname = socket.gethostname()
    pid = os.getpid()
    return f"{hostname}:{pid}"


class LeaseManager:
    """
    Manages distributed lock via AOL lease table.
    
    Safety rules:
    - Lease expires after LEASE_TIMEOUT_SECONDS
    - Renewal must happen before expiration
    - Failed renewal = another daemon owns it (bail out gracefully)
    """
    
    # Lease duration: 30 seconds (must renew every ~10 seconds in normal tick)
    LEASE_TIMEOUT_SECONDS = 30
    
    def __init__(self, db_url: str):
        """Initialize with database connection."""
        self.db_url = db_url
        self.owner = get_daemon_owner()
        self.engine = create_engine(db_url, future=True)
        self.session_maker = sessionmaker(bind=self.engine, expire_on_commit=False)
    
    def acquire_or_renew(self, session: Session) -> Tuple[bool, str]:
        """
        Attempt to acquire or renew lease.
        
        Returns:
            (success: bool, message: str)
            - (True, "Lease acquired") - First claim
            - (True, "Lease renewed") - Renewed by same owner
            - (False, "Lease held by other: owner:pid") - Another daemon owns it
            - (False, "DB error: ...") - Technical failure
        """
        try:
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.LEASE_TIMEOUT_SECONDS)
            
            # Query existing lease
            stmt = select(AOLLease).limit(1)
            existing_lease = session.execute(stmt).scalar_one_or_none()
            
            if existing_lease is None:
                # No lease exists: acquire
                new_lease = AOLLease(
                    owner=self.owner,
                    acquired_at_utc=now,
                    renewed_at_utc=now,
                    expires_at_utc=expires_at,
                )
                session.add(new_lease)
                session.commit()
                return True, "Lease acquired"
            
            # Lease exists
            if existing_lease.expires_at_utc <= now:
                # Expired: claim it
                existing_lease.owner = self.owner
                existing_lease.acquired_at_utc = now
                existing_lease.renewed_at_utc = now
                existing_lease.expires_at_utc = expires_at
                session.commit()
                return True, "Lease acquired (expired holder evicted)"
            
            if existing_lease.owner == self.owner:
                # Same owner: renew
                existing_lease.renewed_at_utc = now
                existing_lease.expires_at_utc = expires_at
                session.commit()
                return True, "Lease renewed"
            
            # Lease held by another daemon
            return False, f"Lease held by other: {existing_lease.owner}"
        
        except Exception as e:
            return False, f"DB error: {str(e)}"
    
    def release(self, session: Session) -> bool:
        """Release lease (daemon shutting down cleanly)."""
        try:
            stmt = select(AOLLease).where(AOLLease.owner == self.owner).limit(1)
            lease = session.execute(stmt).scalar_one_or_none()
            
            if lease:
                session.delete(lease)
                session.commit()
                return True
            return False
        except Exception:
            return False
