#!/usr/bin/env python3
"""
AOL Health CLI - Inspect daemon state without running ticks.

Reads:
- Last tick timestamp + status
- Current lease owner + renewal time
- Control flags (paused, killed)
- Action queue counts (pending, retry, DLQ)

Does not require LLM or Streamlit imports.
Masks sensitive information.
"""

import os
import sys
from datetime import datetime, timezone
from tabulate import tabulate

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

try:
    from aicmo.orchestration.models import (
        AOLTickLedger,
        AOLLease,
        AOLControlFlags,
        AOLAction,
    )
except ImportError as e:
    print(f"Error: Cannot import AOL models: {e}", file=sys.stderr)
    sys.exit(1)


def mask_url(url: str) -> str:
    """Mask sensitive parts of database URL."""
    if not url:
        return "(not set)"
    # postgresql://user:pass@host/db -> postgresql://***:***@host/db
    try:
        import re
        masked = re.sub(r'://[^:]+:[^@]+@', '://***:***@', url)
        return masked
    except:
        return url


def get_health_status(db_url: str = None):
    """Get health status of AOL daemon."""
    if not db_url:
        db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)
    
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        print("\n" + "=" * 70)
        print("AICMO AOL HEALTH STATUS")
        print("=" * 70 + "\n")
        
        # Database info
        print(f"Database: {mask_url(db_url)}")
        print(f"Queried at: {datetime.now(timezone.utc).isoformat()}\n")
        
        # Last tick
        print("LAST TICK:")
        last_tick = session.query(AOLTickLedger).order_by(
            AOLTickLedger.tick_timestamp.desc()
        ).first()
        
        if last_tick:
            print(f"  Timestamp: {last_tick.tick_timestamp}")
            print(f"  Status:    {last_tick.status}")
            print(f"  Actions:   {last_tick.actions_attempted} attempted, {last_tick.actions_succeeded} succeeded")
            print(f"  Duration:  {last_tick.duration_seconds:.2f}s")
            if last_tick.error_notes:
                print(f"  Error:     {last_tick.error_notes[:100]}")
            
            # Time since last tick
            now = datetime.now(timezone.utc)
            delta = now - last_tick.tick_timestamp
            print(f"  Age:       {delta.total_seconds():.0f}s ago")
        else:
            print("  (No ticks recorded yet)")
        
        # Lease status
        print("\nLEASE (Distributed Lock):")
        lease = session.query(AOLLease).first()
        if lease and lease.owner:
            print(f"  Owner:     {lease.owner}")
            print(f"  Held at:   {lease.acquired_at}")
            print(f"  Expires:   {lease.expires_at}")
            
            if lease.expires_at > datetime.now(timezone.utc):
                seconds_left = (lease.expires_at - datetime.now(timezone.utc)).total_seconds()
                print(f"  Time left: {seconds_left:.0f}s")
            else:
                print(f"  Status:    EXPIRED (daemon may be stuck)")
        else:
            print(f"  Owner:     (no lease held)")
        
        # Control flags
        print("\nCONTROL FLAGS:")
        flags = session.query(AOLControlFlags).filter_by(id=1).first()
        if flags:
            print(f"  Paused:    {flags.paused}")
            print(f"  Killed:    {flags.killed}")
            print(f"  PROOF mode: {flags.proof_mode}")
        else:
            print(f"  (not configured)")
        
        # Queue metrics
        print("\nACTION QUEUE:")
        pending_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status == 'PENDING'
        ).scalar() or 0
        
        retry_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status == 'RETRY'
        ).scalar() or 0
        
        dlq_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status == 'DLQ'
        ).scalar() or 0
        
        success_count = session.query(func.count(AOLAction.id)).filter(
            AOLAction.status == 'SUCCESS'
        ).scalar() or 0
        
        print(f"  Pending:   {pending_count}")
        print(f"  Retry:     {retry_count}")
        print(f"  DLQ:       {dlq_count}")
        print(f"  Succeeded: {success_count}")
        
        session.close()
        engine.dispose()
        
        print("\n" + "=" * 70 + "\n")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(get_health_status())
