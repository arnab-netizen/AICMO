"""
Worker locking mechanism for single-worker safety.

Ensures only one CAM worker is active at a time using database advisory locks.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)


def acquire_worker_lock(session: Session, worker_id: str, ttl_minutes: int = 5) -> bool:
    """
    Acquire exclusive lock for worker.
    
    Returns True if lock acquired, False if another worker is active.
    Uses database row-level locking via heartbeat table.
    """
    try:
        from aicmo.cam.db_models import CamWorkerHeartbeatDB
        
        # Try to find existing lock
        existing_lock = session.query(CamWorkerHeartbeatDB).filter(
            CamWorkerHeartbeatDB.status == 'RUNNING'
        ).first()
        
        if existing_lock:
            # Check if it's stale (TTL expired)
            age = datetime.utcnow() - existing_lock.last_seen_at
            if age < timedelta(minutes=ttl_minutes):
                logger.warning(
                    f"Worker {existing_lock.worker_id} holds active lock "
                    f"(age: {age.total_seconds():.0f}s)"
                )
                return False
            
            # Lock is stale, take over
            logger.info(f"Acquiring lock from stale worker {existing_lock.worker_id}")
            existing_lock.status = 'DEAD'
            session.commit()
        
        # Create/update heartbeat with our worker_id
        heartbeat = CamWorkerHeartbeatDB(
            worker_id=worker_id,
            last_seen_at=datetime.utcnow(),
            status='RUNNING',
        )
        session.add(heartbeat)
        session.commit()
        
        logger.info(f"✓ Lock acquired for worker {worker_id}")
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to acquire lock: {str(e)}", exc_info=True)
        return False


def release_worker_lock(session: Session, worker_id: str) -> bool:
    """Release lock held by worker."""
    try:
        from aicmo.cam.db_models import CamWorkerHeartbeatDB
        
        heartbeat = session.query(CamWorkerHeartbeatDB).filter(
            CamWorkerHeartbeatDB.worker_id == worker_id
        ).first()
        
        if heartbeat:
            heartbeat.status = 'STOPPED'
            session.commit()
            logger.info(f"✓ Lock released for worker {worker_id}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"✗ Failed to release lock: {str(e)}", exc_info=True)
        return False


def is_worker_lock_held(session: Session) -> bool:
    """Check if any worker currently holds lock."""
    try:
        from aicmo.cam.db_models import CamWorkerHeartbeatDB
        
        running = session.query(CamWorkerHeartbeatDB).filter(
            CamWorkerHeartbeatDB.status == 'RUNNING'
        ).first()
        
        return running is not None
    
    except Exception as e:
        logger.error(f"✗ Failed to check lock: {str(e)}", exc_info=True)
        return False
