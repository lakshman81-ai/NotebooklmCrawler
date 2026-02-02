"""
DuckDuckGo Search Scraper Module

Purpose: Discover URLs by scraping DuckDuckGo search results.
DuckDuckGo is more bot-friendly than Google, making it the preferred choice.

Advantages:
- No CAPTCHA in most cases
- Simpler HTML structure
- Privacy-respecting (no tracking)
"""

import logging
import re
from urllib.parse import quote, urlparse, parse_qs, unquote
from typing import List, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Blocked URL patterns
BLOCKED_PATTERNS = [
    r"duckduckgo\.com",
    r"youtube\.com",
    r"facebook\.com",
    r"twitter\.com",
    r"instagram\.com",
    r"pinterest\.com",
    r"linkedin\.com",
    r"amazon\.com",
]


async def scrape_ddg_search(
    page: Page,
    query: str,
    max_results: int = 10,
    region: str = "us-en"
) -> List[str]:
    """
    Scrape DuckDuckGo search results using browser automation.

    Args:
        page: Playwright Page object
        query: Search query string
        max_results: Maximum number of URLs to return
        region: DDG region code (default: us-en)

    Returns:
        List of discovered URLs
    """
    logger.info(f"DDG scraping: '{query}' (max={max_results})")

    # Build search URL (HTML version, not JS)
    search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"

    try:
        # Navigate to DDG
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Anti-bot: small delay
        await page.wait_for_timeout(1000)

        # Wait for results or CAPTCHA
        try:
            # Check for CAPTCHA first or concurrent with results
            # We wait for either results or anomaly modal
            await page.wait_for_selector(".result, .results_links, .anomaly-modal__title", timeout=10000)

            content = await page.content()
            if "anomaly-modal__title" in content or "Unfortunately, bots use DuckDuckGo too" in content:
                logger.error("DuckDuckGo CAPTCHA detected")
                raise RuntimeError("DuckDuckGo CAPTCHA blocked the request")

        except Exception as e:
            if "CAPTCHA" in str(e):
                raise
            logger.warning(f"DDG results container not found: {e}")

        # Extract URLs
        urls = await _extract_urls(page, max_results)

        # Filter blocked domains
        filtered_urls = _filter_urls(urls)

        logger.info(f"Discovered {len(urls)} URLs, {len(filtered_urls)} after filtering")
        return filtered_urls[:max_results]

    except Exception as e:
        logger.error(f"DDG scraping failed: {e}")
        raise


async def _extract_urls(page: Page, max_results: int) -> List[str]:
    """Extract URLs from DDG result links."""
    urls = []

    # DDG HTML version uses specific classes
    selectors = [
        ".result__a[href]",            # Primary result links
        ".result__url[href]",          # URL display links
        "a[data-testid='result-title-a']",  # Modern DDG
        ".links_main a[href]",         # Alternative structure
    ]

    for selector in selectors:
        try:
            links = await page.locator(selector).all()

            for link in links:
                if len(urls) >= max_results * 2:
                    break

                try:
                    href = await link.get_attribute("href")

                    # DDG sometimes wraps URLs in redirects
                    actual_url = _unwrap_ddg_redirect(href)

                    if actual_url and actual_url.startswith("http") and actual_url not in urls:
                        urls.append(actual_url)
                except:
                    continue

            if urls:
                break

        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue

    return urls


def _unwrap_ddg_redirect(url: str) -> Optional[str]:
    """
    Unwrap DDG redirect URLs to get the actual destination.

    DDG sometimes uses: //duckduckgo.com/l/?uddg=https%3A%2F%2Factual-url.com
    """
    if not url:
        return None

    # Handle protocol-relative URLs
    if url.startswith("//"):
        url = "https:" + url

    # Check for DDG redirect wrapper
    if "duckduckgo.com/l/" in url or "uddg=" in url:
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if "uddg" in params:
                return unquote(params["uddg"][0])
        except:
            pass

    return url


def _filter_urls(urls: List[str]) -> List[str]:
    """Filter out blocked URLs."""
    filtered = []

    for url in urls:
        is_blocked = False
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, url, re.I):
                is_blocked = True
                break

        if not is_blocked:
            filtered.append(url)

    return filtered


async def scrape_ddg_with_site_filter(
    page: Page,
    query: str,
    domains: List[str],
    max_results: int = 10
) -> List[str]:
    """
    Search DDG with site filters for trusted domains.

    Args:
        page: Playwright Page
        query: Base search query
        domains: List of domains to search within
        max_results: Max results to return

    Returns:
        List of URLs from specified domains
    """
    if not domains:
        return await scrape_ddg_search(page, query, max_results)

    # Build query with site filters
    site_filters = " OR ".join([f"site:{d}" for d in domains])
    full_query = f"{query} ({site_filters})"

    return await scrape_ddg_search(page, full_query, max_results)
