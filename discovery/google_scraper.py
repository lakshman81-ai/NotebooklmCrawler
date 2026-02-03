"""
Google Search Scraper Module

Purpose: Discover educational URLs by scraping Google search results.
Uses Playwright browser automation to avoid API costs.

WARNING: Google may rate-limit or CAPTCHA heavy usage.
Consider using DDG (Phase 3) as primary, Google as fallback.
"""

import logging
import re
from urllib.parse import quote, urlparse
from typing import List, Optional
from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Blocked URL patterns (not educational content)
BLOCKED_PATTERNS = [
    r"google\.com",
    r"youtube\.com",  # Videos don't work well for text extraction
    r"facebook\.com",
    r"twitter\.com",
    r"instagram\.com",
    r"pinterest\.com",
    r"linkedin\.com",
    r"amazon\.com",
    r"ebay\.com",
]


async def scrape_google_search(
    page: Page,
    query: str,
    max_results: int = 10,
    safe_search: bool = True
) -> List[str]:
    """
    Scrape Google search results using browser automation.

    Args:
        page: Playwright Page object (must be from existing browser context)
        query: Search query string
        max_results: Maximum number of URLs to return
        safe_search: Enable SafeSearch filter

    Returns:
        List of discovered URLs (filtered for educational content)

    Raises:
        RuntimeError: If navigation fails or CAPTCHA detected
    """
    logger.info(f"Google scraping: '{query}' (max={max_results})")

    # Build search URL
    safe_param = "&safe=active" if safe_search else ""
    search_url = f"https://www.google.com/search?q={quote(query)}{safe_param}"

    try:
        # Navigate to Google
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Anti-bot: random delay
        await page.wait_for_timeout(1500 + (hash(query) % 1000))

        # Handle consent dialog (GDPR regions)
        await _handle_consent_dialog(page)

        # Check for CAPTCHA
        if await _is_captcha_present(page):
            logger.error("CAPTCHA detected on Google - cannot proceed")
            raise RuntimeError("Google CAPTCHA detected. Try DDG instead.")

        # Wait for results to load
        try:
            await page.wait_for_selector("div#search, div#rso", timeout=10000)
        except:
            logger.warning("Search results container not found")

        # Extract URLs
        urls = await _extract_urls(page, max_results)

        # Filter blocked domains
        filtered_urls = _filter_urls(urls)

        logger.info(f"Discovered {len(urls)} URLs, {len(filtered_urls)} after filtering")
        return filtered_urls[:max_results]

    except Exception as e:
        logger.error(f"Google scraping failed: {e}")
        raise


async def _handle_consent_dialog(page: Page) -> None:
    """Handle Google's GDPR consent dialog if present."""
    consent_buttons = [
        "button:has-text('Accept all')",
        "button:has-text('I agree')",
        "button:has-text('Accept')",
        "button[aria-label*='Accept']",
    ]

    for selector in consent_buttons:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await page.wait_for_timeout(1000)
                logger.debug("Dismissed consent dialog")
                return
        except:
            continue


async def _is_captcha_present(page: Page) -> bool:
    """Check if Google is showing a CAPTCHA."""
    captcha_indicators = [
        "iframe[src*='recaptcha']",
        "div#captcha",
        "form[action*='sorry']",
        "text=unusual traffic",
    ]

    for indicator in captcha_indicators:
        try:
            if await page.locator(indicator).is_visible(timeout=1000):
                return True
        except:
            continue

    return False


async def _extract_urls(page: Page, max_results: int) -> List[str]:
    """Extract URLs from search result links."""
    urls = []

    # Multiple selector strategies for resilience
    selectors = [
        "a[href^='http'][data-ved]",  # Main result links
        "div.g a[href^='http']",       # Fallback: result containers
        "a[href^='http']:not([href*='google'])",  # Broader fallback
    ]

    for selector in selectors:
        try:
            links = await page.locator(selector).all()

            for link in links:
                if len(urls) >= max_results * 2:  # Get extra for filtering
                    break

                try:
                    href = await link.get_attribute("href")
                    if href and href.startswith("http") and href not in urls:
                        urls.append(href)
                except:
                    continue

            if urls:
                break  # Found results with this selector

        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue

    return urls


def _filter_urls(urls: List[str]) -> List[str]:
    """Filter out non-educational and blocked URLs."""
    filtered = []

    for url in urls:
        # Skip blocked patterns
        is_blocked = False
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, url, re.I):
                is_blocked = True
                break

        if not is_blocked:
            filtered.append(url)

    return filtered


async def build_educational_query(
    topic: str,
    grade: str,
    keywords: Optional[List[str]] = None,
    trusted_domains: Optional[List[str]] = None
) -> str:
    """
    Build an optimized educational search query.

    Args:
        topic: Main topic (e.g., "Gravity")
        grade: Grade level (e.g., "Grade 8")
        keywords: Additional keywords to include
        trusted_domains: List of domains to prioritize (uses OR)

    Returns:
        Optimized search query string
    """
    parts = [topic, grade]

    if keywords:
        parts.extend(keywords[:3])  # Limit keywords

    # Add educational qualifiers
    parts.append("educational OR lesson OR tutorial")

    # Add site filters if provided
    if trusted_domains:
        site_filters = " OR ".join([f"site:{d}" for d in trusted_domains[:5]])
        parts.append(f"({site_filters})")

    return " ".join(parts)
