from capsule_core.run import RunRequest, RunResponse, StatusResponse
from capsule_core.metrics import get_registry
from capsule_core.logging import get_logger


def test_imports_and_basics():
    _ = RunRequest(project_id="p1", payload={})
    _ = RunResponse(task_id="t1")
    _ = StatusResponse(task_id="t1", state="QUEUED")
    reg = get_registry()
    reg.counter("jobs").inc()
    reg.histogram("latency").observe(0.01)
    log = get_logger("test")
    log.info("ok")
