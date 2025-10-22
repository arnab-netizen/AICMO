from capsule_core.run import RunRequest, RunResponse, StatusResponse


def test_contract_models_exist():
    # basic type construction (ensures capsule_core wiring)
    _ = RunRequest(project_id="p", payload={})
    _ = RunResponse(task_id="t1")
    _ = StatusResponse(task_id="t1", state="QUEUED")


def test_run_and_status_flow(client):
    r = client.post("/sitegen/run", json={"project_id": "p1", "payload": {"x": 1}})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "task_id" in data and data["accepted"] is True

    st = client.get(f"/sitegen/status/{data['task_id']}")
    assert st.status_code == 200
    s = st.json()
    assert s["state"] in ("RUNNING", "DONE")
    assert s["result"]["ok"] is True


def test_feedback_and_metrics(client):
    fb = client.post("/sitegen/feedback", json={"thumb": "up"})
    assert fb.status_code == 200
    mx = client.get("/sitegen/metrics")
    assert mx.status_code == 200
    j = mx.json()
    assert j["module"] == "sitegen"
