import requests
import json
import sys
import os

API_BASE = "http://localhost:8000"

def test_proxy_headers():
    url = "https://raw.githubusercontent.com/lakshman81-ai/Kani-Worksheet-App/0bd194c14b6404074ad288447f8f8c18c3f9acdb/public/Worksheet%201%20-%20Verbs/questions.csv"
    print(f"Testing Proxy Headers with URL: {url}")
    response = requests.get(f"{API_BASE}/api/proxy/headers", params={"url": url})
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert "headers" in data
    assert "structure" in data
    print("Proxy Headers OK")

def test_read_nested_template():
    # Test reading one of the files we downloaded
    filepath = "Kani/Worksheet/Verbs/questions.csv"
    print(f"Testing Read Template: {filepath}")
    response = requests.post(f"{API_BASE}/api/template/read", json={"filepath": filepath})
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data["filename"] == "questions.csv"
    assert len(data["columns"]) > 0
    print("Read Nested Template OK")

if __name__ == "__main__":
    try:
        test_proxy_headers()
        test_read_nested_template()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
