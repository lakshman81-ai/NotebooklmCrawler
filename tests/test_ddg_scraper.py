"""
Tests for DuckDuckGo Search scraper.
Refactored to test the new `ddgs` library implementation using mocks.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from discovery.ddg_scraper import scrape_ddg_search, scrape_ddg_with_site_filter, _filter_urls

@pytest.mark.asyncio
async def test_ddg_search_basic():
    """Test basic DDG search scraping with mocked DDGS."""

    mock_results = [
        {'href': 'https://www.khanacademy.org/science/grade-8-gravity', 'title': 'Gravity', 'body': '...'},
        {'href': 'https://ck12.org/physics/gravity', 'title': 'Gravity CK12', 'body': '...'}
    ]

    # Mock DDGS context manager
    with patch("discovery.ddg_scraper.DDGS") as MockDDGS:
        instance = MockDDGS.return_value
        # Mock context manager entry/exit
        instance.__enter__.return_value = instance
        instance.__exit__.return_value = None
        # Mock text() method returning an iterator
        instance.text.return_value = iter(mock_results)

        urls = await scrape_ddg_search(
            None, # page is ignored
            "Grade 8 science gravity physics",
            max_results=5
        )

        assert isinstance(urls, list)
        assert len(urls) == 2
        assert "https://www.khanacademy.org/science/grade-8-gravity" in urls
        assert "https://ck12.org/physics/gravity" in urls


@pytest.mark.asyncio
async def test_ddg_with_site_filter():
    """Test DDG search with domain filters."""

    mock_results = [
        {'href': 'https://www.khanacademy.org/science/grade-8-gravity', 'title': 'Gravity', 'body': '...'},
    ]

    with patch("discovery.ddg_scraper.DDGS") as MockDDGS:
        instance = MockDDGS.return_value
        instance.__enter__.return_value = instance
        instance.__exit__.return_value = None
        instance.text.return_value = iter(mock_results)

        urls = await scrape_ddg_with_site_filter(
            None,
            "gravity physics lesson",
            domains=["khanacademy.org"],
            max_results=5
        )

        assert len(urls) == 1
        assert "https://www.khanacademy.org/science/grade-8-gravity" in urls

        # Verify query construction
        call_args = instance.text.call_args
        assert call_args is not None
        # Check that query contains site:khanacademy.org
        # I passed query as first positional argument in discovery/ddg_scraper.py
        query_arg = call_args[0][0]
        assert "gravity physics lesson" in query_arg
        assert "site:khanacademy.org" in query_arg


@pytest.mark.asyncio
async def test_filter_blocked_urls():
    """Test URL filtering."""

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
