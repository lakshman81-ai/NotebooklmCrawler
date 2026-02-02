import pytest
from fastapi.testclient import TestClient
from bridge import app, ENV_PATH
from dotenv import dotenv_values
import os

client = TestClient(app)

def test_save_and_load_config():
    # 1. Save Config
    payload = {
        "maxTokens": 1500,
        "strategy": "fixed_size",
        "outputType": "handout",
        "headless": True,
        "discoveryMethod": "auto",
        "notebooklmAvailable": False,
        "deepseekAvailable": True,
        "notebooklmGuided": True,
        "trustedDomains": "example.com, test.org",
        "blockedDomains": "badsite.com, malware.net"
    }

    response = client.post("/api/config/save", json=payload)
    assert response.status_code == 200
    assert response.json() == {"success": True}

    # 2. Verify .env file content directly (optional, but good)
    # Reload dotenv values from the file
    config = dotenv_values(str(ENV_PATH))
    assert config.get("TRUSTED_DOMAINS") == "example.com, test.org"
    assert config.get("BLOCKED_DOMAINS") == "badsite.com, malware.net"

    # 3. Load Config
    response = client.get("/api/config/load")
    assert response.status_code == 200
    data = response.json()

    assert data["trustedDomains"] == "example.com, test.org"
    assert data["blockedDomains"] == "badsite.com, malware.net"
    assert data["maxTokens"] == 1500
