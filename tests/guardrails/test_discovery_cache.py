from pathlib import Path
import json

CACHE_PATH = Path("outputs/discovery/urls.json")

def test_discovery_cache_exists():
    assert CACHE_PATH.exists(), "Discovery cache missing"

def test_discovery_cache_structure():
    data = json.loads(CACHE_PATH.read_text())
    assert "urls" in data, "Cache missing 'urls' key"
    assert isinstance(data["urls"], list), "'urls' must be a list"
    assert "source" in data
    assert "last_updated" in data
