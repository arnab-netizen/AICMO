from aicmo.api.schemas import ErrorResponse


def test_error_response_shape():
    er = ErrorResponse(error_code="X", message="m", details=None, trace_id="t")
    d = er.dict()
    assert set(d.keys()) == {"error_code", "message", "details", "trace_id"}
