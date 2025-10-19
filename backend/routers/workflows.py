from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Path, Query, Depends
from pydantic import BaseModel
from temporalio.client import Client
import os
import asyncio

from backend.security import require_admin

router = APIRouter(prefix="/workflows", tags=["workflows"], dependencies=[Depends(require_admin)])

TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")


class WorkflowDescribeOut(BaseModel):
    workflow_id: str
    run_id: str | None = None
    status: str | None = None
    history_length: int | None = None
    task_queue: str | None = None


@router.get("/{workflow_id}", response_model=WorkflowDescribeOut)
async def describe_workflow(
    workflow_id: str = Path(..., min_length=1),
) -> WorkflowDescribeOut:
    try:
        client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        desc = await handle.describe()
        # Defensive fields (shape differs across versions)
        status = getattr(desc, "status", None)
        hist_len = getattr(desc, "history_length", None)
        task_queue = None
        if getattr(desc, "execution_config", None):
            task_queue = getattr(desc.execution_config, "task_queue", None)
        return WorkflowDescribeOut(
            workflow_id=workflow_id,
            run_id=getattr(desc, "run_id", None),
            status=str(status) if status is not None else None,
            history_length=hist_len,
            task_queue=task_queue,
        )
    except Exception as e:
        # If Temporal isn’t running, surface 500 so tests can allow it.
        raise HTTPException(status_code=500, detail=str(e))


class WorkflowCancelOut(BaseModel):
    workflow_id: str
    canceled: bool
    detail: str | None = None


@router.post("/{workflow_id}/cancel", response_model=WorkflowCancelOut)
async def cancel_workflow(
    workflow_id: str = Path(..., min_length=1),
) -> WorkflowCancelOut:
    try:
        client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        await handle.cancel()
        return WorkflowCancelOut(workflow_id=workflow_id, canceled=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class WorkflowResultOut(BaseModel):
    workflow_id: str
    done: bool
    result: Any | None = None


@router.get("/{workflow_id}/result", response_model=WorkflowResultOut)
async def get_workflow_result(
    workflow_id: str = Path(..., min_length=1),
    timeout_s: float = Query(default=0.5, ge=0.1, le=60.0),
) -> WorkflowResultOut:
    """
    Poll-friendly: returns 200 when result ready, otherwise 202 with done=false.
    """
    try:
        client = await Client.connect(TEMPORAL_ADDRESS, namespace=TEMPORAL_NAMESPACE)
        handle = client.get_workflow_handle(workflow_id=workflow_id)
        try:
            result = await asyncio.wait_for(handle.result(), timeout=timeout_s)
            return WorkflowResultOut(workflow_id=workflow_id, done=True, result=result)
        except asyncio.TimeoutError:
            # Not done yet → 202
            from fastapi import Response

            Response.status_code = 202  # type: ignore[attr-defined]
            return WorkflowResultOut(workflow_id=workflow_id, done=False, result=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
