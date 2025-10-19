import time
import logging
from fastapi import FastAPI
from backend.core.config import settings
from backend.db import ping_db
from backend.routers.health import router as health_router
from backend.routers.test import router as test_router
from backend.modules.sitegen.routes import router as sitegen_router

log = logging.getLogger("uvicorn.error")

app = FastAPI(title=settings.APP_NAME)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(test_router, tags=["test"])
app.include_router(sitegen_router, prefix="/sitegen", tags=["sitegen"])


@app.on_event("startup")
def startup():
    # Retry for a bounded time so dev server doesn't crash if DB is late
    deadline = time.time() + settings.DB_STARTUP_RETRY_SECS
    logged_once = False
    while time.time() < deadline:
        if ping_db():
            log.info("Database reachable.")
            return
        if not logged_once:
            log.warning("Database not reachable yet; will retry until ready...")
            logged_once = True
        time.sleep(1.0)
    # Out of budget: continue to serve liveness, but readiness will be false
    log.error("Database not reachable within startup budget; continuing without DB.")
