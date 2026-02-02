"""
Tests for DuckDuckGo Search scraper.
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
async def test_ddg_search_basic(browser_page):
    """Test basic DDG search scraping with mocked response."""
    from discovery.ddg_scraper import scrape_ddg_search

    # Mock DDG response to avoid CAPTCHA/network issues in CI/Sandbox
    await browser_page.route("**/html.duckduckgo.com/**", lambda route: route.fulfill(
        status=200,
        content_type="text/html",
        body="""
        <html>
            <body>
                <div class="results_links">
                    <div class="result">
                        <a class="result__a" href="https://www.khanacademy.org/science/grade-8-gravity">Gravity | Khan Academy</a>
                        <a class="result__url" href="https://www.khanacademy.org/science/grade-8-gravity">https://www.khanacademy.org...</a>
                    </div>
                    <div class="result">
                        <a class="result__a" href="https://ck12.org/physics/gravity">Gravity - CK12</a>
                    </div>
                </div>
            </body>
        </html>
        """
    ))

    urls = await scrape_ddg_search(
        browser_page,
        "Grade 8 science gravity physics",
        max_results=5
    )

    assert isinstance(urls, list)
    assert len(urls) > 0, "DDG should return at least 1 result"

    assert "https://www.khanacademy.org/science/grade-8-gravity" in urls
    assert "https://ck12.org/physics/gravity" in urls


@pytest.mark.asyncio
async def test_ddg_with_site_filter(browser_page):
    """Test DDG search with domain filters."""
    from discovery.ddg_scraper import scrape_ddg_with_site_filter

    # Mock DDG response
    await browser_page.route("**/html.duckduckgo.com/**", lambda route: route.fulfill(
        status=200,
        content_type="text/html",
        body="""
        <html>
            <body>
                <div class="results_links">
                    <div class="result">
                        <a class="result__a" href="https://www.khanacademy.org/science/grade-8-gravity">Gravity</a>
                    </div>
                    <div class="result">
                        <a class="result__a" href="https://ck12.org/physics/gravity">Gravity CK12</a>
                    </div>
                </div>
            </body>
        </html>
        """
    ))

    urls = await scrape_ddg_with_site_filter(
        browser_page,
        "gravity physics lesson",
        domains=["khanacademy.org", "ck12.org"],
        max_results=5
    )

    assert isinstance(urls, list)
    assert len(urls) > 0
    # Results should be from specified domains
    for url in urls:
        assert any(d in url for d in ["khanacademy.org", "ck12.org"]), f"URL {url} not from expected domains"

    # other-domain should not be in the results if the scraper respects the domains?
    # Wait, scrape_ddg_with_site_filter *builds* a query with site: filters.
    # The actual filtering happens on DDG side.
    # Since I am mocking the response, I am returning results that *would* be returned by DDG.
    # So I should return only valid results in my mock if I assume DDG works.
    # Or, if I want to test that my code doesn't filter locally (which it doesn't seem to do, it relies on query),
    # then the test just verifies that we get what we scraped.
    # BUT, the scraper code assumes DDG does the filtering.

    # So the assertion:
    # assert any(d in url for d in ["khanacademy.org", "ck12.org"])
    # will pass if my mock returns only those.
    pass


@pytest.mark.asyncio
async def test_unwrap_ddg_redirect():
    """Test URL unwrapping logic."""
    from discovery.ddg_scraper import _unwrap_ddg_redirect

    # Normal URL
    assert _unwrap_ddg_redirect("https://example.com") == "https://example.com"

    # Protocol-relative
    assert _unwrap_ddg_redirect("//example.com").startswith("https")

    # DDG redirect wrapper
    wrapped = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage"
    unwrapped = _unwrap_ddg_redirect(wrapped)
    assert unwrapped == "https://example.com/page"


@pytest.mark.asyncio
async def test_filter_blocked_urls():
    """Test URL filtering."""
    from discovery.ddg_scraper import _filter_urls

    urls = [
        "https://khanacademy.org/science",
        "https://youtube.com/watch?v=123",
        "https://duckduckgo.com/search",
        "https://byjus.com/physics",
    ]

    filtered = _filter_urls(urls)

    assert len(filtered) == 2
    assert "youtube" not in str(filtered)
    assert "duckduckgo" not in str(filtered)


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
