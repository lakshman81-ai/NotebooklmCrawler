import pytest
import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from bridge import app
from run import DISCOVERY_CACHE_PATH

client = TestClient(app)

@pytest.fixture
def mock_pipeline_execution(monkeypatch):
    """
    Mock the actual subprocess call in bridge.py to avoid running the full heavy pipeline
    during this integration test, but verify the API contract works.
    """
    async def mock_subprocess_exec(*args, **kwargs):
        # Simulate successful process creation
        mock_process = asyncio.Future()
        mock_process.set_result(None)
        return mock_process

    # We need to mock asyncio.create_subprocess_exec used in bridge.py
    # However, since bridge.py imports asyncio, we might need to patch it there.
    # Given TestClient runs synchronously, testing async subprocess in bridge via TestClient is tricky.
    # Instead, we will test the /api/auto/execute endpoint logic up to the subprocess call.
    pass

def test_api_config_load():
    """Verify backend config loading works (used by frontend)."""
    response = client.get("/api/config/load")
    assert response.status_code == 200
    data = response.json()
    assert "maxTokens" in data
    assert "discoveryMethod" in data
    print("\nConfig Load Response:", data)

def test_api_execute_request_flow():
    """
    Simulate the frontend sending an execution request.
    Verifies the backend accepts the payload and sets up the environment.
    """
    payload = {
        "targetUrl": "",
        "grade": "Grade 8",
        "topic": "Photosynthesis",
        "subtopics": "Process, Importance",
        "materialType": "study_material",
        "customPrompt": "",
        "sourceType": "trusted",
        "config": {
            "headless": True,
            "maxTokens": 1000,
            "discoveryMethod": "Auto", # Should trigger DDG/Google
            "outputs": {"studyGuide": True},
            "quizConfig": {"mcq": 5}
        }
    }

    try:
        response = client.post("/api/auto/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "snapshotId" in data
        print("\nExecute Response:", data)

        # Verify ENV variables were set (side effect of bridge.py)
        # bridge.py sets keys in .env and os.environ
        # We check os.environ to see if the request updated the state
        assert os.environ.get("CR_TOPIC") == "Photosynthesis"
        assert os.environ.get("DISCOVERY_METHOD") == "auto"

    except Exception as e:
        pytest.fail(f"API Execute failed: {e}")

def test_config_persistence():
    """
    Verify that config changes are persisted to the .env file on disk.
    This addresses the 'Configuration Logic' finding.
    """
    # Create/check .env
    env_path = Path(".env")
    if not env_path.exists():
        env_path.touch()

    # Send a config save request
    new_config = {
        "maxTokens": 9999,
        "strategy": "fixed_size",
        "outputType": "handout",
        "headless": True,
        "discoveryMethod": "google",
        "notebooklmAvailable": False,
        "deepseekAvailable": True,
        "notebooklmGuided": False
    }

    response = client.post("/api/config/save", json=new_config)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Check if .env file actually contains the new values
    content = env_path.read_text()
    assert "MAX_TOKENS='9999'" in content or 'MAX_TOKENS="9999"' in content or "MAX_TOKENS=9999" in content
    assert "DISCOVERY_METHOD='google'" in content or 'DISCOVERY_METHOD="google"' in content or "DISCOVERY_METHOD=google" in content

    print("\nConfig Persistence Verified: .env file updated correctly.")

def test_observability_logs_streaming():
    """
    Verify that logs written to logs/app.log are retrievable via /api/logs.
    This addresses the 'Observability' finding.
    """
    log_file = Path("logs/app.log")
    if not log_file.parent.exists():
        log_file.parent.mkdir(parents=True)

    # Write a unique log entry
    unique_msg = "TEST_LOG_ENTRY_OBSERVABILITY_CHECK"
    log_entry = json.dumps({"timestamp": "2099-01-01T00:00:00", "level": "INFO", "message": unique_msg}) + "\n"

    with open(log_file, "a") as f:
        f.write(log_entry)

    # Retrieve logs via API
    response = client.get("/api/logs")
    assert response.status_code == 200
    data = response.json()

    # Check if our unique message is in the response
    found = False
    for entry in data["logs"]:
        if isinstance(entry, dict) and entry.get("message") == unique_msg:
            found = True
            break

    assert found, "Unique log entry not found in API response"
    print("\nObservability Verified: Backend logs are streaming to API.")
