import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from discovery.ddg_scraper import scrape_ddg_search
from crawler.discovery_router import discover_urls, filter_urls
from run import update_discovery_cache, get_target_urls
from contracts.source_policy import SourceType
from postprocess.composer import compose_output
from contracts.output_schema import FinalOutput

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

@pytest.mark.asyncio
async def test_discovery_fallback_logic():
    """
    Simulate a primary scraper failure (mocked) and verify fallback is triggered.
    This addresses the 'Robustness' requirement explicitly.
    """
    print("\nTesting Discovery Fallback Logic...")

    # We want to test: Primary (Google) -> Fails -> Fallback (DDG) -> Succeeds

    # Mock Google Scraper (Simulate Failure)
    mock_google = AsyncMock(side_effect=RuntimeError("Simulated Google Failure"))

    # Mock DDG Scraper (Simulate Success)
    mock_ddg = AsyncMock(return_value=["https://fallback-result.com/ddg"])

    # Patch the scrapers INSIDE discovery_router where they are imported locally
    # Note: Since they are local imports, patching them directly via 'discovery.google_scraper.scrape_google_search' works
    # IF the function hasn't been imported yet, or if we patch the module itself.

    with patch("discovery.google_scraper.scrape_google_search", mock_google):
        with patch("discovery.ddg_scraper.scrape_ddg_search", mock_ddg):

            # Request 'google' method
            urls = await discover_urls(None, "test query", method="google")

            # Verify results came from Fallback (DDG)
            assert len(urls) == 1
            assert urls[0] == "https://fallback-result.com/ddg"

            # Verify primary was called
            mock_google.assert_called_once()

            # Verify fallback was called
            mock_ddg.assert_called_once()

            print("Fallback Triggered Successfully: Google (Failed) -> DDG (Success)")

def test_composer_output_formatting():
    """
    Verify postprocess.composer correctly handles different output types.
    """
    print("\nTesting Composer Output Formatting...")

    ai_result = {
        "summary": "This is a summary.",
        "evidence": "Some evidence here."
    }

    # Test 'study_material'
    output = compose_output(ai_result, "study_material")
    assert output["metadata"]["output_type"] == "study_material"
    assert output["summary"] == "This is a summary."
    assert output["content"] == ai_result

    # Test 'quiz'
    output_quiz = compose_output(ai_result, "quiz")
    assert output_quiz["metadata"]["output_type"] == "quiz"

    print("Composer Output Formatting Verified.")
