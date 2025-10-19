from fastapi import APIRouter, Response, status
from backend.db import ping_db

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
