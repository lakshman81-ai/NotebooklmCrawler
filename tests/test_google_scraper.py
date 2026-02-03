"""
Tests for Google Search scraper.
Requires active browser context.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright


@pytest.fixture
async def browser_page():
    """Provide a browser page for testing."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        yield page
        await browser.close()


@pytest.mark.asyncio
async def test_google_search_basic(browser_page):
    """Test basic Google search scraping."""
    from discovery.google_scraper import scrape_google_search

    try:
        urls = await scrape_google_search(
            browser_page,
            "Grade 8 science gravity site:khanacademy.org",
            max_results=3
        )

        # May return 0 if CAPTCHA'd
        assert isinstance(urls, list)
        if urls:
            assert all(url.startswith("http") for url in urls)
            assert all("google.com" not in url for url in urls)

    except RuntimeError as e:
        if "CAPTCHA" in str(e):
            pytest.skip("Google CAPTCHA detected - expected in automated tests")
        raise


@pytest.mark.asyncio
async def test_build_educational_query():
    """Test query builder."""
    from discovery.google_scraper import build_educational_query

    query = await build_educational_query(
        topic="Gravity",
        grade="Grade 8",
        keywords=["mass", "weight"],
        trusted_domains=["khanacademy.org", "ck12.org"]
    )

    assert "Gravity" in query
    assert "Grade 8" in query
    assert "site:khanacademy.org" in query
    assert "OR" in query


@pytest.mark.asyncio
async def test_filter_blocked_urls():
    """Test URL filtering."""
    from discovery.google_scraper import _filter_urls

    urls = [
        "https://khanacademy.org/science/gravity",
        "https://youtube.com/watch?v=123",
        "https://google.com/search?q=test",
        "https://byjus.com/physics/gravity",
    ]

    filtered = _filter_urls(urls)

    assert len(filtered) == 2
    assert "khanacademy.org" in filtered[0]
    assert "byjus.com" in filtered[1]


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
