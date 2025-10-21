def test_materialize_persists_in_memory(client):
    spec = {
        "site": {"name": "Founder OS"},
        "pages": [{"slug": "home"}, {"slug": "about"}],
    }
    r = client.post("/sitegen/materialize", json=spec)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["site"] == "founder-os"
    assert data["pages"] == ["home", "about"]
