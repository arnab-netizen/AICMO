"""
Smoke test: Backend /health/aol endpoint is reachable and returns valid JSON.

CRITICAL: Streamlit must be able to query this endpoint without DB credentials.
"""
import pytest
from starlette.testclient import TestClient


@pytest.mark.smoke
def test_health_aol_endpoint_exists(client):
    """
    Verify /health/aol endpoint exists and returns valid response.
    
    This is critical for Streamlit to display AOL status without DB access.
    """
    response = client.get("/health/aol")
    
    # Should return 200 (OK) or 503 (DB unavailable) - both are valid responses
    assert response.status_code in [200, 503], f"Unexpected status: {response.status_code}"
    
    # Response must be JSON
    data = response.json()
    assert isinstance(data, dict), "Response must be JSON object"
    
    # Required fields (may be null if DB unavailable)
    if response.status_code == 200:
        assert "last_tick_at" in data
        assert "last_tick_status" in data
        assert "lease_owner" in data
        assert "flags" in data
        assert "queue_counts" in data
        assert "server_time_utc" in data
        
        # Flags must be a dict
        if data["flags"]:
            assert isinstance(data["flags"], dict)
            assert "paused" in data["flags"]
            assert "killed" in data["flags"]
            assert "proof_mode" in data["flags"]
        
        # Queue counts must be a dict
        if data["queue_counts"]:
            assert isinstance(data["queue_counts"], dict)
            assert "pending" in data["queue_counts"]
            assert "retry" in data["queue_counts"]
            assert "dlq" in data["queue_counts"]


@pytest.mark.smoke
def test_health_aol_endpoint_no_secrets_leaked(client):
    """
    Verify /health/aol does not leak database URLs or API keys.
    """
    response = client.get("/health/aol")
    
    text = response.text.lower()
    
    # Should NOT contain DB credentials
    assert "postgresql://" not in text, "Database URL leaked in response"
    assert "password" not in text, "Password keyword in response"
    assert "api_key" not in text, "API key in response"
    assert "openai" not in text, "OpenAI key reference in response"


@pytest.mark.smoke
def test_health_aol_endpoint_read_only(client):
    """
    Verify /health/aol is read-only (GET only).
    """
    # POST should not be allowed
    response = client.post("/health/aol", json={})
    assert response.status_code in [405, 404], "POST should not be allowed"
    
    # PUT should not be allowed
    response = client.put("/health/aol", json={})
    assert response.status_code in [405, 404], "PUT should not be allowed"
    
    # DELETE should not be allowed
    response = client.delete("/health/aol")
    assert response.status_code in [405, 404], "DELETE should not be allowed"
