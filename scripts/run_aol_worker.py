#!/usr/bin/env python3
"""
Render Background Worker for AICMO AOL (Autonomy Orchestration Layer)

Runs as a continuous long-running process on Render's Worker tier.
Executes AOL ticks indefinitely, respecting database lease and control flags.

Does NOT require OpenAI, Streamlit, or UI imports at module level.
Does NOT auto-start daemon (manual trigger via API or Render dashboard).
"""

import os
import sys
import time
import logging
import signal
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional

# Must be importable WITHOUT OpenAI key
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

# Import AOL components
try:
    from aicmo.orchestration.daemon import AOLDaemon
    from aicmo.orchestration.models import AOLTickLedger, AOLControlFlags, AOLLease
except ImportError as e:
    print(f"FATAL: Cannot import AOL modules: {e}", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)

# Configuration (from environment)
DATABASE_URL = os.getenv('DATABASE_URL')
AOL_TICK_INTERVAL_SECONDS = int(os.getenv('AOL_TICK_INTERVAL_SECONDS', '30'))
AOL_MAX_ACTIONS_PER_TICK = int(os.getenv('AOL_MAX_ACTIONS_PER_TICK', '3'))
AOL_MAX_TICK_SECONDS = int(os.getenv('AOL_MAX_TICK_SECONDS', '20'))
AOL_PROOF_MODE = os.getenv('AOL_PROOF_MODE', 'true').lower() == 'true'

# Graceful shutdown
shutdown_requested = False

def handle_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT gracefully."""
    global shutdown_requested
    shutdown_requested = True
    log.info(f"Shutdown signal {signum} received. Finishing current tick...")


def validate_config():
    """Validate required configuration."""
    if not DATABASE_URL:
        log.error("FATAL: DATABASE_URL not set")
        sys.exit(1)
    
    if not DATABASE_URL.startswith('postgresql://'):
        log.error("FATAL: Only PostgreSQL supported (DATABASE_URL must start with postgresql://)")
        sys.exit(1)
    
    log.info(f"AOL Worker Configuration:")
    log.info(f"  Tick interval: {AOL_TICK_INTERVAL_SECONDS}s")
    log.info(f"  Max actions/tick: {AOL_MAX_ACTIONS_PER_TICK}")
    log.info(f"  Max tick duration: {AOL_MAX_TICK_SECONDS}s")
    log.info(f"  PROOF mode: {AOL_PROOF_MODE}")


def create_db_engine():
    """Create SQLAlchemy engine for database access."""
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Test connections before using
            echo=False,
        )
        # Verify connection
        with engine.connect() as conn:
            conn.execute(select(1))
        log.info("✓ Database connection verified")
        return engine
    except Exception as e:
        log.error(f"FATAL: Cannot connect to database: {e}")
        sys.exit(1)


@contextmanager
def get_session(engine):
    """Context manager for database sessions."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_daemon_control_flags(session: Session) -> tuple[bool, bool]:
    """
    Check AOL control flags: (paused, killed)
    
    Returns:
        (paused, killed): If killed=True, worker should exit cleanly.
    """
    try:
        flags = session.query(AOLControlFlags).filter_by(id=1).first()
        if not flags:
            return False, False
        return flags.paused, flags.killed
    except Exception as e:
        log.warning(f"Cannot check control flags: {e}")
        return False, False


def run_single_tick(daemon: AOLDaemon, session: Session) -> dict:
    """
    Run a single AOL tick.
    
    Returns:
        dict: Tick result with keys:
          - status: 'SUCCESS', 'PARTIAL', 'FAIL'
          - actions_attempted: int
          - actions_succeeded: int
          - duration_seconds: float
          - error: Optional[str]
    """
    start_time = time.time()
    
    try:
        # Run tick (respects lease, flags, etc.)
        tick_result = daemon.run(max_ticks=1)
        
        duration = time.time() - start_time
        
        # Classify result
        if tick_result.get('exit_code') == 0:
            status = 'SUCCESS'
        else:
            status = 'PARTIAL'
        
        result = {
            'status': status,
            'actions_attempted': tick_result.get('actions_attempted', 0),
            'actions_succeeded': tick_result.get('actions_succeeded', 0),
            'duration_seconds': duration,
            'error': None,
        }
    except Exception as e:
        duration = time.time() - start_time
        log.error(f"Tick execution error: {e}")
        result = {
            'status': 'FAIL',
            'actions_attempted': 0,
            'actions_succeeded': 0,
            'duration_seconds': duration,
            'error': str(e)[:200],
        }
    
    return result


def log_tick_to_ledger(session: Session, tick_result: dict):
    """Record tick result in aol_tick_ledger."""
    try:
        ledger_entry = AOLTickLedger(
            tick_timestamp=datetime.now(timezone.utc),
            status=tick_result['status'],
            actions_attempted=tick_result['actions_attempted'],
            actions_succeeded=tick_result['actions_succeeded'],
            duration_seconds=tick_result['duration_seconds'],
            error_notes=tick_result['error'],
        )
        session.add(ledger_entry)
        session.commit()
    except Exception as e:
        log.warning(f"Cannot log tick to ledger: {e}")
        session.rollback()


def run_worker_loop(engine):
    """
    Main worker loop: run ticks indefinitely.
    
    Respects:
    - Database lease (distributed lock)
    - Control flags (pause, kill)
    - Graceful shutdown (SIGTERM)
    """
    log.info("Starting AOL Worker infinite loop...")
    
    daemon = AOLDaemon(db_url=DATABASE_URL, proof_mode=AOL_PROOF_MODE)
    
    tick_count = 0
    
    while not shutdown_requested:
        tick_count += 1
        
        with get_session(engine) as session:
            # Check control flags
            paused, killed = check_daemon_control_flags(session)
            
            if killed:
                log.info("Kill flag set. Exiting gracefully.")
                return 0
            
            if paused:
                log.debug("Daemon paused. Sleeping...")
                time.sleep(5)
                continue
        
        # Run tick
        with get_session(engine) as session:
            tick_result = run_single_tick(daemon, session)
            log.info(
                f"[Tick {tick_count}] {tick_result['status']} | "
                f"Actions: {tick_result['actions_attempted']} attempted, "
                f"{tick_result['actions_succeeded']} succeeded | "
                f"Duration: {tick_result['duration_seconds']:.2f}s"
            )
            
            # Log to database
            log_tick_to_ledger(session, tick_result)
        
        # Sleep before next tick
        if not shutdown_requested:
            time.sleep(AOL_TICK_INTERVAL_SECONDS)
    
    log.info("Shutdown requested. Exiting gracefully.")
    return 0


def main():
    """Entry point for Render worker."""
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    log.info("=" * 70)
    log.info("AICMO AOL Worker Starting")
    log.info("=" * 70)
    
    # Validate
    validate_config()
    
    # Create database engine
    engine = create_db_engine()
    
    try:
        # Run worker loop
        exit_code = run_worker_loop(engine)
        log.info("Worker exited successfully.")
        return exit_code
    except KeyboardInterrupt:
        log.info("Keyboard interrupt received.")
        return 0
    except Exception as e:
        log.error(f"FATAL: Unhandled exception: {e}", exc_info=True)
        return 1
    finally:
        engine.dispose()


if __name__ == '__main__':
    sys.exit(main())
