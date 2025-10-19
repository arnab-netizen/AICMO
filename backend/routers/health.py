from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import sqlalchemy as sa
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
