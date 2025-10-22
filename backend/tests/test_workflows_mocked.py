# backend/tests/test_workflows_mocked.py
from types import SimpleNamespace
import asyncio


# ---- Fake Temporal client/handle --------------------------------------------
class FakeHandle:
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id

    async def describe(self):
        # mimic Temporal's describe fields that your router reads
        return SimpleNamespace(
            run_id="fake-run-id",
            status="COMPLETED",
            history_length=3,
            execution_config=SimpleNamespace(task_queue="sitegen"),
        )

    async def cancel(self):
        return None

    async def result(self):
        # immediately "complete" with a small payload
        await asyncio.sleep(0)  # yield
        return {"ok": True, "workflow_id": self.workflow_id}


class FakeClient:
    def __init__(self):
        pass

    def get_workflow_handle(self, workflow_id: str):
        return FakeHandle(workflow_id)


# ---- Async factory to replace Client.connect --------------------------------
async def fake_connect(addr: str, namespace: str):
    assert addr  # just to match signature
    assert namespace
    return FakeClient()


def test_workflows_routes_with_mock(monkeypatch, client):
    # Patch temporalio.client.Client.connect to our fake_connect
    import temporalio.client as tclient

    monkeypatch.setattr(tclient.Client, "connect", staticmethod(fake_connect))

    # Describe
    r = client.get("/workflows/sitegen-123")
    assert r.status_code == 200
    body = r.json()
    assert body["workflow_id"] == "sitegen-123"
    assert body["status"] in ("COMPLETED", "completed")

    # Result (ready)
    r = client.get("/workflows/sitegen-123/result?timeout_s=0.1")
    assert r.status_code == 200
    body = r.json()
    assert body["done"] is True
    assert body["result"]["ok"] is True

    # Cancel
    r = client.post("/workflows/sitegen-123/cancel")
    assert r.status_code == 200
    body = r.json()
    assert body["canceled"] is True
