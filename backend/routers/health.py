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


@router.head("/health/ready")
def readiness_head():
    # Fast path for HEAD probes: return 200 or 503 with no body
    return Response(status_code=200 if ping_db() else status.HTTP_503_SERVICE_UNAVAILABLE)
