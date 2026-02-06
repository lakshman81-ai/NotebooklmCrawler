"""
Bing Search Scraper Module (Replaces DDG)

Purpose: Discover URLs by scraping Bing search results via Playwright + Firefox.
Replaced `ddgs` with `EducationalContentSearcher` from `discovery/bing_search.py`.
"""

import logging
import asyncio
from typing import List
from playwright.async_api import Page
from discovery.bing_search import EducationalContentSearcher

logger = logging.getLogger(__name__)

async def scrape_ddg_search(
    page: Page, # Unused, kept for interface compatibility
    query: str,
    max_results: int = 10,
    region: str = "us-en"
) -> List[str]:
    """
    Scrape search results using EducationalContentSearcher (Bing + Firefox).

    Args:
        page: Playwright Page object (ignored, as EducationalContentSearcher manages its own browser)
        query: Search query string
        max_results: Maximum number of URLs to return
        region: Region code (ignored in this implementation, defaults to Bing's auto-detect or US)

    Returns:
        List of discovered URLs
    """
    logger.info(f"Bing scraping (via EducationalContentSearcher): '{query}' (max={max_results})")

    def _perform_search():
        searcher = EducationalContentSearcher(
            headless=True,
            config_file='outputs/search_config.json',
            cache_dir='outputs/search_cache'
        )
        try:
            # Ensure we start the browser
            searcher.start()

            # Use search_bing for generic queries
            results = searcher.search_bing(query, count=max_results)
            return [r['url'] for r in results]
        except Exception as e:
            logger.error(f"EducationalContentSearcher failed: {e}")
            return []
        finally:
            searcher.close()

    # Run the blocking search in a thread to avoid blocking the async event loop
    urls = await asyncio.to_thread(_perform_search)

    logger.info(f"Discovered {len(urls)} URLs")
    for url in urls[:max_results]:
        logger.info(f"Discovered URL: {url}")

    return urls[:max_results]


async def scrape_ddg_with_site_filter(
    page: Page,
    query: str,
    domains: List[str],
    max_results: int = 10
) -> List[str]:
    """
    Search Bing with site filters for trusted domains.
    """
    if not domains:
        return await scrape_ddg_search(page, query, max_results)

    # Build query with site filters
    # Bing supports (site:domain OR site:domain2)
    site_filters = " OR ".join([f"site:{d}" for d in domains])
    full_query = f"{query} ({site_filters})"

    return await scrape_ddg_search(page, full_query, max_results)
