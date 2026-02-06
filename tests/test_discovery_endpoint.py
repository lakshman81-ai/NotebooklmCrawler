import pytest
from fastapi.testclient import TestClient
from bridge import app

client = TestClient(app)

def test_discovery_fetch_endpoint():
    # This test assumes ddgs is working and network is available.
    # If network is not available, it might fail or return empty.
    # We just want to check if the endpoint is reachable and returns the correct structure.

    response = client.post("/api/discovery/fetch", json={
        "grade": "8",
        "subject": "Science",
        "topic": "Photosynthesis",
        "maxResults": 1
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "results" in data
    assert isinstance(data["results"], list)
    # Ideally checking if len(results) > 0, but it depends on external service.
    # Based on previous CLI test, it should work.
