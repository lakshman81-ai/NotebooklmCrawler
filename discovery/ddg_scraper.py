"""
DuckDuckGo Search Scraper Module

Purpose: Discover URLs by scraping DuckDuckGo search results.
Refactored to use `ddgs` library (formerly duckduckgo_search) for better reliability and performance.
"""

import logging
import re
import os
import asyncio
from typing import List, Optional
from ddgs import DDGS
from playwright.async_api import Page

logger = logging.getLogger(__name__)

def _load_blocked_patterns():
    # Load blocked domains from environment variable
    env_patterns = os.getenv("BLOCKED_DOMAINS", "")
    if env_patterns:
        patterns = [re.escape(p.strip()) for p in env_patterns.split(",") if p.strip()]
        if patterns:
            return patterns

    return [
        r"duckduckgo\.com",
        r"youtube\.com",
        r"facebook\.com",
        r"twitter\.com",
        r"instagram\.com",
        r"pinterest\.com",
        r"linkedin\.com",
        r"amazon\.com",
    ]

# Blocked URL patterns
BLOCKED_PATTERNS = _load_blocked_patterns()

def _perform_ddg_search(query: str, max_results: int, region: str) -> List[str]:
    """
    Synchronous function to perform the actual search using DDGS.
    """
    urls = []
    try:
        # standard timeout
        with DDGS(timeout=20) as ddgs:
            # text() returns a generator
            results_gen = ddgs.text(
                query,
                region=region,
                safesearch='moderate',
                timelimit='y', # limit to past year for relevance
                max_results=max_results
            )

            for r in results_gen:
                href = r.get('href')
                if href:
                    urls.append(href)

    except Exception as e:
        logger.error(f"DDGS execution failed: {e}")

    return urls

def _filter_urls(urls: List[str]) -> List[str]:
    """Filter out blocked URLs."""
    filtered = []
    patterns = BLOCKED_PATTERNS

    for url in urls:
        is_blocked = False
        for pattern in patterns:
            if re.search(pattern, url, re.I):
                is_blocked = True
                break

        if not is_blocked:
            filtered.append(url)

    return filtered

async def scrape_ddg_search(
    page: Page, # Unused, kept for interface compatibility
    query: str,
    max_results: int = 10,
    region: str = "us-en"
) -> List[str]:
    """
    Scrape DuckDuckGo search results using ddgs library.

    Args:
        page: Playwright Page object (ignored in this implementation)
        query: Search query string
        max_results: Maximum number of URLs to return
        region: DDG region code (default: us-en)

    Returns:
        List of discovered URLs
    """
    logger.info(f"DDG scraping: '{query}' (max={max_results})")

    # Run the blocking search in a thread
    raw_urls = await asyncio.to_thread(_perform_ddg_search, query, max_results, region)

    # Filter blocked domains
    filtered_urls = _filter_urls(raw_urls)

    logger.info(f"Discovered {len(raw_urls)} URLs, {len(filtered_urls)} after filtering")

    # Log individually for frontend visibility (Discovery Feed)
    for url in filtered_urls[:max_results]:
        logger.info(f"Discovered URL: {url}")

    return filtered_urls[:max_results]


async def scrape_ddg_with_site_filter(
    page: Page,
    query: str,
    domains: List[str],
    max_results: int = 10
) -> List[str]:
    """
    Search DDG with site filters for trusted domains.
    """
    if not domains:
        return await scrape_ddg_search(page, query, max_results)

    # Build query with site filters
    # DDG supports site:domain OR site:domain2
    site_filters = " OR ".join([f"site:{d}" for d in domains])
    full_query = f"{query} ({site_filters})"

    return await scrape_ddg_search(page, full_query, max_results)
