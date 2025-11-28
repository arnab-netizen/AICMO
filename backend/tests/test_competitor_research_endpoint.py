"""Tests for /api/competitor/research endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Fixture to provide FastAPI test client."""
    from backend.main import app

    return TestClient(app)


class TestCompetitorResearchEndpoint:
    """Test suite for competitor research API endpoint."""

    def test_competitor_research_missing_required_fields(self, client):
        """Should return error when industry or location missing."""
        payload = {"industry": "Technology"}
        response = client.post("/api/competitor/research", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["competitors"] == []

    def test_competitor_research_with_location_and_industry(self, client):
        """Should return competitors list when industry and location provided."""
        payload = {
            "industry": "Technology",
            "location": "San Francisco",
        }
        response = client.post("/api/competitor/research", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "competitors" in data
        assert isinstance(data["competitors"], list)

    def test_competitor_research_response_structure(self, client):
        """Verify response always has expected structure."""
        payload = {
            "industry": "Healthcare",
            "location": "Boston",
        }
        response = client.post("/api/competitor/research", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "competitors" in data
        assert data["status"] in ["ok", "error"]
        assert isinstance(data["competitors"], list)
