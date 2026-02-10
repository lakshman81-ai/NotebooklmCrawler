"""
Discovery Manager Module

Purpose:
- Unified interface for URL discovery.
- Implements "Gold Standard" robustness:
  1. Primary: DuckDuckGo API (Fast, No Auth, High Quota)
  2. Fallback: Google Custom Search JSON API (Reliable, Auth Required)
- Handles errors and logging gracefully.
"""

import os
import logging
from typing import List, Optional
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class SearchManager:
    """
    Manages search operations with automatic fallback strategies.
    """

    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cx = os.getenv("GOOGLE_SEARCH_CX")

    def search(self, query: str, max_results: int = 10, method: str = "auto") -> List[str]:
        """
        Perform a search using the specified method or auto-fallback.

        Args:
            query: The search query.
            max_results: Maximum number of URLs to return.
            method: 'auto', 'ddg', or 'google'.

        Returns:
            List of discovered URLs.
        """
        method = method.lower()
        logger.info(f"SearchManager: Requesting '{query}' (limit={max_results}, method={method})")

        if method == "google":
            return self._search_google(query, max_results)
        elif method == "ddg":
            return self._search_ddg(query, max_results)
        else: # Auto
            # Strategy: Try DDG first (free/fast), fallback to Google (paid/limited)
            try:
                results = self._search_ddg(query, max_results)
                if results:
                    return results
                logger.warning("SearchManager: DDG returned no results. Falling back to Google.")
            except Exception as e:
                logger.error(f"SearchManager: DDG failed ({e}). Falling back to Google.")

            # Fallback
            return self._search_google(query, max_results)

    def _search_ddg(self, query: str, max_results: int) -> List[str]:
        """
        Search using DuckDuckGo (via ddgs package).
        """
        try:
            logger.info("SearchManager: Executing DuckDuckGo search...")
            urls = []
            with DDGS() as ddgs:
                # ddgs.text returns an iterator of dicts {'title':..., 'href':..., 'body':...}
                results = ddgs.text(query, max_results=max_results)
                for r in results:
                    urls.append(r['href'])

            logger.info(f"SearchManager: DDG found {len(urls)} URLs")
            return urls
        except Exception as e:
            logger.error(f"SearchManager: DDG Error: {e}")
            raise # Re-raise to trigger fallback in 'auto' mode

    def _search_google(self, query: str, max_results: int) -> List[str]:
        """
        Search using Google Custom Search JSON API.
        """
        if not self.google_api_key or not self.google_cx:
            logger.warning("SearchManager: Google API credentials missing (GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX). Skipping Google search.")
            return []

        try:
            logger.info("SearchManager: Executing Google Custom Search...")
            service = build("customsearch", "v1", developerKey=self.google_api_key)

            # CSE allows max 10 results per page
            # If max_results > 10, we'd need pagination.
            # For this scope, let's cap at 10 per call or loop if needed.
            # Usually discovery is fine with top 10.

            urls = []
            start_index = 1

            while len(urls) < max_results:
                # Calculate how many to fetch (max 10)
                num = min(10, max_results - len(urls))

                res = service.cse().list(
                    q=query,
                    cx=self.google_cx,
                    num=num,
                    start=start_index
                ).execute()

                items = res.get('items', [])
                if not items:
                    break

                for item in items:
                    urls.append(item['link'])

                start_index += len(items)

                # Check for next page
                if 'nextPage' not in res.get('queries', {}):
                    break

            logger.info(f"SearchManager: Google found {len(urls)} URLs")
            return urls

        except Exception as e:
            logger.error(f"SearchManager: Google Search Error: {e}")
            return [] # Return empty list on Google failure (it's usually the fallback)
