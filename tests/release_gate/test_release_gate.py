import os
import uuid
from fastapi.testclient import TestClient

import operator_v2
from aicmo.ui.persistence.intake_store import IntakeStore
from backend.app import app as backend_app
import os
import uuid
from fastapi.testclient import TestClient

import operator_v2
from aicmo.ui.persistence.intake_store import IntakeStore
from backend.app import app as backend_app


def test_handle_intake_submit_populates_artifact_and_session():
    session = {}
    store = IntakeStore(mode="inmemory")
    payload = {
        "client_name": "Test Client",
        "brand_name": "Test Brand",
        "product_service": "Test Product",
        "raw_brief_text": "This is a test brief",
    }

    artifact = operator_v2.handle_intake_submit(session, payload, store)

    assert artifact["status"] == "SUCCESS"
    assert "client_id" in artifact and isinstance(artifact["client_id"], str)
    assert session.get("active_client_id") == artifact["client_id"]
    assert session.get("artifact_intake") is not None
    assert isinstance(session.get("client_brief"), dict)


def test_store_artifact_from_backend_success_and_error_cases():
    session = {"active_client_id": "cid-1", "active_engagement_id": "eid-1"}

    # success envelope
    envelope = {"deliverables": [{"id": "d1", "title": "T", "content_markdown": "# ok"}], "meta": {}}
    art = operator_v2.store_artifact_from_backend(session, "strategy", envelope)
    assert art["status"] == "SUCCESS"
    assert len(art["deliverables"]) == 1

    # missing content -> error
    bad_env = {"deliverables": [{"id": "d2", "title": "T", "content_markdown": ""}], "meta": {}}
    art2 = operator_v2.store_artifact_from_backend(session, "strategy", bad_env)
    assert art2["status"] == "ERROR"


def test_backend_deterministic_mode_returns_markdown():
    os.environ["AICMO_E2E_DETERMINISTIC"] = "1"
    client = TestClient(backend_app)
    resp = client.post("/aicmo/generate", json={"use_case": "strategy", "brief": "hi"})
    assert resp.status_code == 200
    data = resp.json()
    assert "deliverables" in data
    assert isinstance(data["deliverables"], list)
    assert len(data["deliverables"]) >= 1
    assert data["deliverables"][0]["content_markdown"] is not None and data["deliverables"][0]["content_markdown"] != ""