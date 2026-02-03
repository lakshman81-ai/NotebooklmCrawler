import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from discovery.ddg_scraper import scrape_ddg_search
from crawler.discovery_router import discover_urls, filter_urls
from run import update_discovery_cache, get_target_urls
from contracts.source_policy import SourceType

@pytest.mark.asyncio
async def test_ddg_scraper_direct():
    """Test DDG scraper directly."""
    print("\nTesting DDG Scraper...")
    try:
        urls = await scrape_ddg_search(None, "Force and Pressure Grade 8", max_results=5)
        print(f"DDG URLs found: {len(urls)}")
        for url in urls:
            print(f" - {url}")

        assert len(urls) > 0, "DDG Scraper returned 0 URLs"

    except Exception as e:
        pytest.fail(f"DDG Scraper failed with error: {e}")

@pytest.mark.asyncio
async def test_run_py_logic_flow():
    """Simulate run.py active search mode logic."""
    print("\nTesting run.py logic flow...")

    # Simulate environment
    os.environ["TARGET_URL"] = ""
    os.environ["DISCOVERY_METHOD"] = "ddg"

    # Simulate active search
    query = "Force and Pressure Grade 8"
    print(f"Discovering URLs with method=ddg, query='{query}'")

    discovered_urls = await discover_urls(None, query, method="ddg")
    print(f"Discovered: {len(discovered_urls)}")

    if not discovered_urls:
        print("Discovery returned 0 URLs. Skipping rest of test.")
        return

    # Simulate updating cache
    update_discovery_cache(discovered_urls)

    # Simulate getting target URLs
    try:
        urls = get_target_urls()
        print(f"Retrieved target URLs: {len(urls)}")
        assert len(urls) == len(discovered_urls)
    except RuntimeError as e:
        pytest.fail(f"get_target_urls failed: {e}")

def test_trusted_domain_filtering():
    """Test that filter_urls correctly filters for trusted domains."""
    print("\nTesting Trusted Domain Filtering...")

    mixed_urls = [
        "https://www.khanacademy.org/science/physics",
        "https://byjus.com/physics/force/",
        "https://example.com/blog/physics",
        "https://random-site.org/article",
        "https://vedantu.com/course"
    ]

    # Test Trusted Mode
    trusted_urls = filter_urls(mixed_urls, SourceType.TRUSTED)
    print(f"Trusted Mode URLs: {trusted_urls}")

    expected_trusted = [
        "https://www.khanacademy.org/science/physics",
        "https://byjus.com/physics/force/",
        "https://vedantu.com/course"
    ]

    assert len(trusted_urls) == 3
    for url in expected_trusted:
        assert url in trusted_urls
    assert "https://example.com/blog/physics" not in trusted_urls

    # Test General Mode
    general_urls = filter_urls(mixed_urls, SourceType.GENERAL)
    print(f"General Mode URLs: {general_urls}")
    assert len(general_urls) == 5
