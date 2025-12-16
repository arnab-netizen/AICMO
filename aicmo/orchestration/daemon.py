"""
Autonomy Orchestration Layer Daemon - Main loop runner.

Behavior:
1. Acquire lease (exit if failed)
2. Read control flags
3. If paused: sleep and re-loop
4. If killed: release lease and exit
5. Process up to MAX_ACTIONS_PER_TICK actions
6. Enforce MAX_TICK_SECONDS limit (abort if exceeded)
7. Write tick ledger row
8. Repeat

Safety limits:
- MAX_ACTIONS_PER_TICK = 3
- MAX_TICK_SECONDS = 20
- MAX_RETRIES = 3 (per action)
- HEARTBEAT_INTERVAL_SECONDS = 5 (renew lease)
"""

import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from aicmo.orchestration.models import AOLControlFlags, AOLTickLedger
from aicmo.orchestration.queue import ActionQueue
from aicmo.orchestration.lease import LeaseManager
from aicmo.orchestration.adapters.social_adapter import handle_post_social, RealRunUnconfigured


class AOLDaemon:
    """Main daemon loop."""
    
    MAX_ACTIONS_PER_TICK = 3
    MAX_TICK_SECONDS = 20
    HEARTBEAT_INTERVAL_SECONDS = 5
    
    def __init__(self, db_url: str):
        """Initialize daemon with database URL."""
        self.db_url = db_url
        self.engine = create_engine(db_url, future=True)
        self.session_maker = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.lease_manager = LeaseManager(db_url)
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.running = False
    
    def run(self, max_ticks: Optional[int] = None) -> int:
        """
        Run daemon loop.
        
        Args:
            max_ticks: Max iterations (None = run forever)
        
        Returns:
            Exit code (0 = success, 1 = failure)
        """
        tick_count = 0
        session = self.session_maker()
        
        try:
            while self.running:
                if max_ticks and tick_count >= max_ticks:
                    break
                
                # Acquire/renew lease
                success, msg = self.lease_manager.acquire_or_renew(session)
                if not success:
                    print(f"[AOL] Lease failed: {msg}. Exiting.", file=sys.stderr)
                    return 1
                
                # Run one tick
                tick_status = self._run_tick(session, tick_count)
                
                if tick_status == "KILLED":
                    print("[AOL] Killed flag detected. Shutting down.", file=sys.stderr)
                    break
                
                tick_count += 1
                
                # Brief sleep before next tick
                time.sleep(0.1)
            
            # Clean shutdown
            self.lease_manager.release(session)
            return 0
        
        except KeyboardInterrupt:
            print("[AOL] Interrupted by user.", file=sys.stderr)
            self.lease_manager.release(session)
            return 1
        
        except Exception as e:
            print(f"[AOL] Fatal error: {str(e)}", file=sys.stderr)
            self.lease_manager.release(session)
            return 1
        
        finally:
            session.close()
    
    def _run_tick(self, session: Session, tick_number: int) -> str:
        """
        Execute one daemon tick.
        
        Returns:
            "NORMAL" or "KILLED"
        """
        tick_started = datetime.utcnow()
        actions_attempted = 0
        actions_succeeded = 0
        tick_status = "SUCCESS"
        tick_notes = ""
        
        try:
            # Read control flags
            stmt = select(AOLControlFlags).limit(1)
            flags = session.execute(stmt).scalar_one_or_none()
            
            if not flags:
                # Initialize default flags
                flags = AOLControlFlags()
                session.add(flags)
                session.commit()
            
            # Check for pause
            if flags.paused:
                return "NORMAL"  # Skip this tick
            
            # Check for kill
            if flags.killed:
                return "KILLED"
            
            # Read control again to get proof_mode
            proof_mode = flags.proof_mode
            
            # Dequeue next actions
            actions = ActionQueue.dequeue_next(session, max_actions=self.MAX_ACTIONS_PER_TICK)
            
            for action in actions:
                # Check tick timeout
                elapsed = (datetime.utcnow() - tick_started).total_seconds()
                if elapsed >= self.MAX_TICK_SECONDS:
                    tick_notes = f"Tick timeout reached after {elapsed:.1f}s. Stopping action processing."
                    tick_status = "PARTIAL"
                    break
                
                actions_attempted += 1
                
                try:
                    # Dispatch action
                    if action.action_type == "POST_SOCIAL":
                        import json
                        payload = json.loads(action.payload_json) if action.payload_json else {}
                        payload["idempotency_key"] = action.idempotency_key
                        handle_post_social(session, action.id, payload, proof_mode=proof_mode)
                        actions_succeeded += 1
                    else:
                        # Unknown action type
                        error_msg = f"Unknown action type: {action.action_type}"
                        ActionQueue.log_execution(session, action.id, "ERROR", error_msg)
                        ActionQueue.mark_failed(session, action.id, error_msg)
                
                except RealRunUnconfigured:
                    # Expected error in REAL mode
                    pass
                
                except Exception as e:
                    # Action failed
                    error_msg = f"Action execution error: {str(e)}"
                    ActionQueue.log_execution(session, action.id, "ERROR", error_msg)
                    ActionQueue.mark_retry(session, action.id, error_msg)
        
        except Exception as e:
            tick_status = "FAIL"
            tick_notes = f"Tick critical error: {str(e)}"
        
        finally:
            # Write tick ledger
            tick_finished = datetime.utcnow()
            
            ledger = AOLTickLedger(
                started_at_utc=tick_started,
                finished_at_utc=tick_finished,
                status=tick_status,
                notes=tick_notes,
                actions_attempted=actions_attempted,
                actions_succeeded=actions_succeeded,
            )
            session.add(ledger)
            session.commit()
            
            print(
                f"[AOL Tick {tick_number}] {tick_status} | "
                f"Actions: {actions_attempted} attempted, {actions_succeeded} succeeded | "
                f"Duration: {(tick_finished - tick_started).total_seconds():.2f}s",
                file=sys.stderr
            )
            
            return "NORMAL"


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "sqlite:////tmp/aol.db")
    daemon = AOLDaemon(db_url)
    exit_code = daemon.run()
    sys.exit(exit_code)
