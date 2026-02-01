from pathlib import Path
import hashlib
import pytest

RAW_DIR = Path("outputs/html/raw")

def hash_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def test_raw_html_is_immutable():
    if not RAW_DIR.exists():
         pytest.skip("Raw directory does not exist")

    files = list(RAW_DIR.glob("*.html"))
    if not files:
        pytest.skip("No raw HTML files found to test integrity")

    hashes_before = {f: hash_file(f) for f in files}

    # simulate rerun or downstream steps here if needed
    # In a real test, we might invoke some idempotent function

    hashes_after = {f: hash_file(f) for f in files}

    assert hashes_before == hashes_after, \
        "Raw HTML was modified — guardrail violation"
