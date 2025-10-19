from fastapi import APIRouter, Response, status, Depends
from backend.db import ping_db, get_db, exec_sql, get_engine
from sqlalchemy import text

router = APIRouter()


@router.get("/health/live")
def liveness():
    # Process is up and serving HTTP
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(response: Response):
    if ping_db():
        return {"status": "ready"}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready", "reason": "db_unreachable"}


@router.get("/health/db")
def db_health(response: Response, db=Depends(get_db)):
    # First, try a low-level engine-based check so tests that monkeypatch
    # engine.begin() are detected (these simulate a DB down scenario).
    try:
        eng = get_engine()
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"status": "error", "detail": str(e)[:200]}

    try:
        with eng.begin() as cx:
            cx.execute(text("SELECT 1"))
    except Exception:
        # Treat engine-level failures as service-unavailable
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "detail": "engine operation failed"}

    # If the engine-level check passed, also validate the request-scoped
    # session (this covers dependency overrides used in tests).
    try:
        try:
            exec_sql(db, "SELECT 1")
        except Exception:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "detail": str(e)[:200]}
