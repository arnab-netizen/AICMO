from __future__ import annotations

import os
import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from temporalio.client import Client as TemporalClient

router = APIRouter(prefix="/sitegen", tags=["sitegen"])

# --- config ---------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/app")
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")
TASK_QUEUE = os.getenv("SITEGEN_TASK_QUEUE", "sitegen.activities")

_engine: Optional[Engine] = None
_temporal: Optional[TemporalClient] = None


def db() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    return _engine


async def temporal_client() -> TemporalClient:
    global _temporal
    if _temporal is None:
        _temporal = await TemporalClient.connect(TEMPORAL_ADDRESS)
    return _temporal


# --- schemas --------------------------------------------------------
class CreateSiteResp(BaseModel):
    site_id: str


class SpecIn(BaseModel):
    spec: dict = Field(default_factory=dict)
    name: Optional[str] = None  # optional site name override


class SpecResp(BaseModel):
    site_id: str
    version: int


class BuildReq(BaseModel):
    provider: str = Field(default="vercel")  # vercel|netlify|gh-pages
    creds: dict = Field(default_factory=dict)  # store ref/ids, not secrets ideally


class BuildResp(BaseModel):
    workflow_id: str
    run_id: Optional[str] = None


# --- helpers --------------------------------------------------------
def _get_latest_spec(conn, site_id: str) -> Optional[dict]:
    row = conn.execute(
        text(
            """SELECT spec FROM site_spec WHERE site_id=:sid
                ORDER BY version DESC LIMIT 1"""
        ),
        {"sid": site_id},
    ).fetchone()
    return row[0] if row else None


def _next_spec_version(conn, site_id: str) -> int:
    row = conn.execute(
        text("""SELECT COALESCE(MAX(version), 0) FROM site_spec WHERE site_id=:sid"""),
        {"sid": site_id},
    ).fetchone()
    return int(row[0]) + 1


# --- endpoints ------------------------------------------------------
@router.post("/sites/{project_id}", response_model=CreateSiteResp)
def create_site(project_id: str) -> CreateSiteResp:
    with db().begin() as conn:
        row = conn.execute(
            text("INSERT INTO site (project_id) VALUES (:pid) RETURNING id"),
            {"pid": project_id},
        ).fetchone()
        return CreateSiteResp(site_id=str(row[0]))


@router.post("/sites/{site_id}/spec", response_model=SpecResp)
def save_spec(site_id: str, body: SpecIn) -> SpecResp:
    with db().begin() as conn:
        # optional: update name
        if body.name:
            conn.execute(
                text("UPDATE site SET name=:n WHERE id=:sid"), {"n": body.name, "sid": site_id}
            )
        ver = _next_spec_version(conn, site_id)
        conn.execute(
            text(
                """INSERT INTO site_spec (site_id, version, spec)
                    VALUES (:sid, :ver, :spec::jsonb)"""
            ),
            {"sid": site_id, "ver": ver, "spec": json.dumps(body.spec)},
        )
        return SpecResp(site_id=site_id, version=ver)


@router.post("/sites/{site_id}/build", response_model=BuildResp)
async def start_build(site_id: str, req: BuildReq) -> BuildResp:
    # fetch latest spec
    with db().begin() as conn:
        spec = _get_latest_spec(conn, site_id)
        if not spec:
            raise HTTPException(
                status_code=400,
                detail="No spec found for site. POST /sitegen/sites/{site_id}/spec first.",
            )

    client = await temporal_client()
    # We use site_id as workflow_id for idempotency; include a short suffix to allow re-runs
    workflow_id = f"sitegen-{site_id}"
    handle = await client.start_workflow(
        "SiteGenWorkflow.run",
        {"site_id": site_id, "spec": spec, "provider": req.provider, "creds": req.creds},
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    run_id = handle.run_id

    with db().begin() as conn:
        conn.execute(
            text(
                """INSERT INTO site_build (site_id, workflow_id, run_id, status)
                    VALUES (:sid, :wid, :rid, 'started')"""
            ),
            {"sid": site_id, "wid": workflow_id, "rid": run_id},
        )

    return BuildResp(workflow_id=workflow_id, run_id=run_id)
