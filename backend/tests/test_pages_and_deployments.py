def test_list_pages_and_deployments_routes_exist(client):
    # pages for a site (may be empty if SiteGen hasn't run)
    r = client.get("/sites/1/pages")
    assert r.status_code in (200, 404)

    # deployments (global and filtered)
    r = client.get("/deployments")
    assert r.status_code == 200
    r = client.get("/deployments?site_id=1")
    assert r.status_code == 200
