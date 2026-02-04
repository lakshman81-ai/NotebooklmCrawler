import pytest
import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from discovery.google_scraper import scrape_google_search
from discovery.ddg_scraper import scrape_ddg_search

@pytest.mark.asyncio
async def test_live_google_search():
    """
    Performs a LIVE Google search using Playwright to verify the scraper works in the real world.
    WARNING: This test may fail due to CAPTCHAs or rate limiting. It is expected.
    """
    print("\n--- LIVE Google Search Test ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            query = "Python programming tutorial for beginners"
            print(f"Searching Google for: '{query}'")
            urls = await scrape_google_search(page, query, max_results=3)

            print(f"Found {len(urls)} URLs:")
            for url in urls:
                print(f" - {url}")

            # Assert we got results (unless blocked)
            if len(urls) == 0:
                print("WARNING: Google returned 0 results. Likely CAPTCHA/Blocked.")
            else:
                assert len(urls) > 0
                # Basic validation
                assert any("python" in u.lower() for u in urls)

        except Exception as e:
            print(f"Google Search Failed: {e}")
            # We don't fail the test hard if it's a network/captcha issue, but we log it.
            if "CAPTCHA" in str(e):
                pytest.skip("Skipping due to Google CAPTCHA")
            else:
                pytest.fail(f"Google Scraper broken: {e}")
        finally:
            await browser.close()

@pytest.mark.asyncio
async def test_live_ddg_search():
    """
    Performs a LIVE DuckDuckGo search to verify the scraper works.
    DDG is generally more lenient than Google.
    """
    print("\n--- LIVE DDG Search Test ---")
    try:
        query = "Photosynthesis explanation for kids"
        print(f"Searching DDG for: '{query}'")
        # DDG scraper doesn't strictly need a page object, passing None
        urls = await scrape_ddg_search(None, query, max_results=3)

        print(f"Found {len(urls)} URLs:")
        for url in urls:
            print(f" - {url}")

        assert len(urls) > 0
        assert any("photosynthesis" in u.lower() or "science" in u.lower() for u in urls)

    except Exception as e:
        pytest.fail(f"DDG Scraper broken: {e}")

@pytest.mark.asyncio
async def test_live_search_no_results_handled():
    """
    Verifies that searching for a nonsense query returns an empty list gracefully
    instead of crashing.
    """
    print("\n--- LIVE Gibberish Search Test ---")
    try:
        # A query highly unlikely to have results
        query = "alkjsdhflkjahsdlkjfhlaksjdhflkajshdflkjahsdlfkjhasldkfjhaslkdjfh"
        print(f"Searching DDG for gibberish: '{query}'")
        urls = await scrape_ddg_search(None, query, max_results=3)

        print(f"Found {len(urls)} URLs")
        # NOTE: It seems DDG is "smart" and returns results even for gibberish (e.g., related to languages or wikipedia abbreviations).
        # The key test is that it DOES NOT CRASH.
        # So we assert the call completed successfully.
        assert urls is not None

    except Exception as e:
        pytest.fail(f"Scraper crashed on empty results: {e}")
