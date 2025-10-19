from fastapi import APIRouter, Response, status
from backend.db import ping_db
from backend.db import get_engine
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
def db_health(response: Response):
    try:
        eng = get_engine()
    except Exception:
        # Could not obtain engine -> server error
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"ok": False}
    try:
        with eng.begin() as cx:
            cx.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception:
        # DB operation failed; mark as service unavailable
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"ok": False}
