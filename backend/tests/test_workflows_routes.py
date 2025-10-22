def test_workflows_routes_exist_and_respond(client):
    # Describe (may 500 if Temporal is down; route must exist)
    r = client.get("/workflows/sitegen-1")
    assert r.status_code in (200, 500)

    # Cancel (same tolerance)
    r = client.post("/workflows/sitegen-1/cancel")
    assert r.status_code in (200, 500)

    # Result polling (200 if ready, 202 if pending, 500 if Temporal absent)
    r = client.get("/workflows/sitegen-1/result?timeout_s=0.1")
    assert r.status_code in (200, 202, 500)
