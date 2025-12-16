from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import select, func
from backend.db import get_engine, get_db

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/health/db")
def health_db(request: Request):
    # Prefer an engine-level begin() check so callers (and tests) that
    # simulate failure by monkeypatching Engine.begin() are detected.
    try:
        eng = get_engine()
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)[:200]})

    try:
        with eng.begin() as cx:
            cx.execute(sa.text("SELECT 1"))
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)[:200]})

    # Try to obtain a request-scoped session. Prefer an app-level dependency override
    # so tests can inject broken sessions.
    db = None

    def close_fn():
        return None

    override = getattr(request.app, "dependency_overrides", {}).get(get_db)
    if override:
        try:
            gen_or_val = override()
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"status": "error", "detail": str(e)[:200]}
            )
        # If the override returned a generator, get the yielded session
        try:
            db = next(gen_or_val)
            close_fn = getattr(gen_or_val, "close", lambda: None)
        except TypeError:
            # Not a generator, treat as direct value
            db = gen_or_val
    else:
        try:
            gen = get_db()
            db = next(gen)
            close_fn = getattr(gen, "close", lambda: None)
        except Exception as e:
            return JSONResponse(
                status_code=500, content={"status": "error", "detail": str(e)[:200]}
            )

    try:
        try:
            # Prefer a helper that may exist; use text for raw SQL safety
            db.execute(sa.text("SELECT 1"))
        except Exception as e:
            return JSONResponse(
                status_code=503, content={"status": "error", "detail": str(e)[:200]}
            )
    finally:
        try:
            close_fn()
        except Exception:
            pass

    return {"db_ok": True}


@router.get("/health/aol")
def health_aol(request: Request):
    """
    AOL Health Status Endpoint
    
    Returns:
    - last_tick_at: ISO timestamp of last AOL tick
    - last_tick_status: 'SUCCESS', 'PARTIAL', 'FAIL', or null
    - lease_owner: Current lease owner (worker ID or null)
    - flags: {paused, killed, proof_mode}
    - queue_counts: {pending, retry, dlq, succeeded}
    - server_time_utc: Current server timestamp
    - status: 200 if OK, 503 if database unavailable
    """
    try:
        eng = get_engine()
        with eng.begin() as cx:
            cx.execute(sa.text("SELECT 1"))
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "detail": f"Database unavailable: {str(e)[:100]}",
                "server_time_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    try:
        # Get session
        override = getattr(request.app, "dependency_overrides", {}).get(get_db)
        if override:
            gen = override()
            try:
                db = next(gen)
            except TypeError:
                db = gen
        else:
            gen = get_db()
            db = next(gen)
        
        # Query AOL state
        from aicmo.orchestration.models import (
            AOLTickLedger,
            AOLLease,
            AOLControlFlags,
            AOLAction,
        )
        
        # Last tick
        last_tick = db.execute(
            select(AOLTickLedger).order_by(AOLTickLedger.tick_timestamp.desc()).limit(1)
        ).scalar()
        
        last_tick_at = None
        last_tick_status = None
        if last_tick:
            last_tick_at = last_tick.tick_timestamp.isoformat() if last_tick.tick_timestamp else None
            last_tick_status = last_tick.status
        
        # Lease status
        lease = db.execute(select(AOLLease)).scalar()
        lease_owner = lease.owner if lease else None
        
        # Control flags
        flags_row = db.execute(select(AOLControlFlags).filter_by(id=1)).scalar()
        flags = {
            "paused": flags_row.paused if flags_row else False,
            "killed": flags_row.killed if flags_row else False,
            "proof_mode": flags_row.proof_mode if flags_row else True,
        }
        
        # Queue counts
        pending_count = db.execute(
            select(func.count(AOLAction.id)).filter(AOLAction.status == "PENDING")
        ).scalar() or 0
        retry_count = db.execute(
            select(func.count(AOLAction.id)).filter(AOLAction.status == "RETRY")
        ).scalar() or 0
        dlq_count = db.execute(
            select(func.count(AOLAction.id)).filter(AOLAction.status == "DLQ")
        ).scalar() or 0
        success_count = db.execute(
            select(func.count(AOLAction.id)).filter(AOLAction.status == "SUCCESS")
        ).scalar() or 0
        
        queue_counts = {
            "pending": pending_count,
            "retry": retry_count,
            "dlq": dlq_count,
            "succeeded": success_count,
        }
        
        return {
            "last_tick_at": last_tick_at,
            "last_tick_status": last_tick_status,
            "lease_owner": lease_owner,
            "flags": flags,
            "queue_counts": queue_counts,
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
        }
    
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "detail": f"Cannot query AOL state: {str(e)[:100]}",
                "server_time_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
