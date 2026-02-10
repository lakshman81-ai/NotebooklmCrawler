"""
Discovery Router Module

Purpose:
- Routes search queries to the appropriate backend strategy (DDG/Google).
- Handles filtering of URLs (trusted sites, blocked domains).
"""

import logging
import asyncio
from typing import List, Optional
from discovery.search_manager import SearchManager

logger = logging.getLogger(__name__)

async def discover_urls(query: str, max_results: int = 10, method: str = "auto") -> List[str]:
    """
    Discover URLs using the unified SearchManager.

    Args:
        query: Search string
        max_results: Max URLs to return
        method: 'auto' (default), 'google', 'ddg'

    Returns:
        List of discovered URLs
    """
    logger.info(f"DiscoveryRouter: Routing query '{query}' (limit={max_results}, method={method})")

    # Instantiate SearchManager
    search_mgr = SearchManager()

    try:
        # Wrap blocking search in thread
        urls = await asyncio.to_thread(search_mgr.search, query, max_results, method)
        logger.info(f"DiscoveryRouter: Discovered {len(urls)} URLs")
        return urls
    except Exception as e:
        logger.error(f"DiscoveryRouter: Search failed: {e}")
        return []

def filter_urls(urls: List[str], source_type: str = "general") -> List[str]:
    """
    Filters URLs based on trusted domains or blocklists.

    Args:
        urls: List of raw URLs
        source_type: 'trusted' (whitelist) or 'general' (blacklist only)

    Returns:
        Filtered list of URLs
    """
    from contracts.source_policy import TRUSTED_DOMAINS, BLOCKED_DOMAINS

    filtered = []

    source_type = str(source_type).lower()

    for url in urls:
        url_lower = url.lower()

        # 1. Global Blocklist Check
        if any(blocked in url_lower for blocked in BLOCKED_DOMAINS):
            logger.debug(f"Blocked URL (global list): {url}")
            continue

        # 2. Trusted Filtering (If enabled)
        if source_type == "trusted":
            if not any(trusted in url_lower for trusted in TRUSTED_DOMAINS):
                logger.debug(f"Filtered URL (not in trusted list): {url}")
                continue

        filtered.append(url)

    logger.info(f"DiscoveryRouter: Filtered {len(urls)} -> {len(filtered)} URLs (Mode: {source_type})")
    return filtered
