from __future__ import annotations
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from temporalio.client import Client
from backend.sitegen.workflows import SiteGenWorkflow, SiteGenInput, TASK_QUEUE
import os
from sqlalchemy import text
from backend.db import get_engine

router = APIRouter(prefix="/sitegen", tags=["sitegen"])

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")


class SiteGenStart(BaseModel):
    site_id: int | None = None
    slug: str | None = None


@router.post("/start", status_code=202)
async def start_sitegen(payload: SiteGenStart):
    if not payload.site_id and not payload.slug:
        raise HTTPException(status_code=400, detail="Provide site_id or slug")

    site_id = payload.site_id
    if site_id is None and payload.slug:
        with get_engine().begin() as conn:
            row = conn.execute(text("SELECT id FROM site WHERE slug = :s"), {"s": payload.slug}).scalar()
            if not row:
                raise HTTPException(status_code=404, detail="Site not found")
            site_id = int(row)

    try:
        client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
        handle = await client.start_workflow(
            SiteGenWorkflow.run,
            SiteGenInput(site_id=site_id),
            id=f"sitegen-{site_id}",
            task_queue=TASK_QUEUE,
        )
        return {"workflow_id": handle.id, "run_id": handle.result_run_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
