from capsule_core.run import RunRequest, StatusResponse
from capsule_core.metrics import get_registry
from capsule_core.logging import get_logger


def test_capsule_core_wired():
    req = RunRequest(project_id="demo", payload={"x": 1})
    assert req.project_id == "demo"
    assert StatusResponse(task_id="t", state="QUEUED").state == "QUEUED"
    reg = get_registry()
    reg.counter("runs_total").inc()
    get_logger("wire").info("ok")
