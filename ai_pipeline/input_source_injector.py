"""
Module 3A: Input Source Prompt Injector (GUIDED MODE ONLY)

Purpose: DOM automation for NotebookLM source discovery flow.
Handles "Add source" → "Website"/"Search the web" navigation and prompt injection.

This module is ONLY used in GUIDED mode (NOTEBOOKLM_GUIDED=true).
In UNGUIDED mode, chunks are uploaded directly instead.
"""

import re
import logging
from typing import Optional
from playwright.async_api import Page

from prompt_modules import InputSourcePromptBuilder

logger = logging.getLogger(__name__)


class InputSourcePromptInjector:
    """
    Handles GUIDED mode input source prompting via DOM automation.

    Workflow:
        1. Generate optimized search queries (using InputSourcePromptBuilder)
        2. Navigate NotebookLM UI to "Add source"
        3. Inject URL or search query
        4. Wait for source processing
    """

    def __init__(self, page: Page, input_prompt_builder: InputSourcePromptBuilder):
        """
        Initialize the input source injector.

        Args:
            page: Playwright Page object for browser automation
            input_prompt_builder: InputSourcePromptBuilder instance for query generation
        """
        self.page = page
        self.input_builder = input_prompt_builder

        logger.info("InputSourcePromptInjector initialized for GUIDED mode")

    async def inject_source_discovery_prompts(self,
                                             content_request,
                                             target_url: Optional[str] = None) -> bool:
        """
        Execute Source Discovery Flow.

        Args:
            content_request: ContentRequest object or dict
            target_url: Optional URL to add directly (if provided, skips search)

        Returns:
            True if source added successfully, False otherwise

        Workflow:
            - If target_url provided: Add as Website source
            - Else: Perform web search with optimized query
        """
        logger.info("Starting source discovery prompt injection...")

        # Generate optimized search strategy
        search_strategy = self.input_builder.generate_multi_source_strategy()

        logger.debug(f"Search strategy: {list(search_strategy.keys())}")

        if target_url and len(target_url) > 5:
            # Direct URL injection
            logger.info(f"Target URL provided: {target_url}")
            return await self._inject_url_source(target_url)
        else:
            # Multi-tier search approach
            # Use Tier 1: Canonical sources (CK-12, Khan Academy)
            primary_search = search_strategy['primary_search']
            logger.info(f"Using primary search query: {primary_search[:80]}...")
            return await self._inject_search_source(primary_search)

    async def _inject_url_source(self, url: str) -> bool:
        """
        DOM automation to add URL source.

        Based on lines 210-280 logic from current notebooklm.py.

        Args:
            url: The URL to add as a source

        Returns:
            True if URL added successfully
        """
        logger.info(f"Injecting URL source: {url}")

        try:
            # Click "Add source" button
            logger.debug("Looking for 'Add source' button...")
            add_src_btn = self.page.locator("button, div[role='button']").filter(
                has_text=re.compile(r"Add source|Insert", re.I)
            ).last

            if await add_src_btn.is_visible(timeout=5000):
                await add_src_btn.click(force=True)
                await self.page.wait_for_timeout(300)
                logger.debug("Clicked 'Add source' button")
            else:
                logger.warning("'Add source' button not visible")
                return False

            # Select "Website" option
            logger.debug("Looking for 'Website' option...")
            site_option = self.page.locator("button").filter(
                has_text=re.compile(r"Website", re.I)
            ).last

            if await site_option.is_visible(timeout=3000):
                await site_option.click(force=True)
                await self.page.wait_for_timeout(500)
                logger.debug("Clicked 'Website' option")
            else:
                logger.warning("'Website' option not visible")
                return False

            # Fill URL input
            logger.debug("Looking for URL input field...")
            url_input = self.page.locator("input[placeholder*='link'], input[type='url']").first

            if await url_input.is_visible(timeout=3000):
                await url_input.fill(url)
                await self.page.wait_for_timeout(300)
                logger.debug(f"Filled URL input: {url}")
            else:
                logger.warning("URL input field not visible")
                return False

            # Click Insert/Add button
            logger.debug("Looking for 'Insert'/'Add' button...")
            insert_btn = self.page.locator("button").filter(
                has_text=re.compile(r"Insert|Add", re.I)
            ).last

            if await insert_btn.is_visible(timeout=3000):
                await insert_btn.click(force=True)
                logger.info("✓ URL source added successfully")
                await self.page.wait_for_timeout(1000)  # Wait for processing to start
                return True
            else:
                logger.warning("Insert/Add button not visible")
                return False

        except Exception as e:
            logger.error(f"Error injecting URL source: {e}")
            return False

    async def _inject_search_source(self, search_query: str) -> bool:
        """
        DOM automation to perform web search.

        Based on lines 283-340 logic from current notebooklm.py.

        Args:
            search_query: Optimized search query string

        Returns:
            True if search completed and sources imported
        """
        logger.info(f"Injecting search query: {search_query[:100]}...")

        try:
            # Click "Add source" → "Search the web"
            logger.debug("Looking for 'Search the web' option...")

            # First click "Add source" if not already open
            add_src_btn = self.page.locator("button, div[role='button']").filter(
                has_text=re.compile(r"Add source|Insert", re.I)
            ).last

            if await add_src_btn.is_visible(timeout=5000):
                await add_src_btn.click(force=True)
                await self.page.wait_for_timeout(300)
                logger.debug("Clicked 'Add source' button")

            # Now click "Search the web"
            web_option = self.page.locator("button").filter(
                has_text=re.compile(r"Search the web|Web", re.I)
            ).last

            if await web_option.is_visible(timeout=3000):
                await web_option.click(force=True)
                await self.page.wait_for_timeout(500)
                logger.debug("Clicked 'Search the web' option")
            else:
                logger.warning("'Search the web' option not visible")
                return False

            # Fill search input with optimized query
            logger.debug("Looking for search input field...")
            search_input = self.page.locator(
                "input[placeholder*='Search'], textarea[placeholder*='Search']"
            ).first

            if await search_input.is_visible(timeout=3000):
                await search_input.fill(search_query)
                await self.page.keyboard.press("Enter")
                logger.debug(f"Submitted search query: {search_query[:80]}...")
            else:
                logger.warning("Search input field not visible")
                return False

            # Wait for results and import
            logger.info("Waiting for search results...")
            try:
                await self.page.wait_for_selector("text=Select all", timeout=30000)
                logger.debug("Search results loaded")
            except Exception as e:
                logger.error(f"Timeout waiting for search results: {e}")
                return False

            # Select all sources
            logger.debug("Selecting all sources...")
            select_all_checkbox = self.page.locator("input[type='checkbox']").filter(
                has_text=re.compile(r"Select all", re.I)
            ).first

            if await select_all_checkbox.is_visible(timeout=3000):
                await select_all_checkbox.click()
                await self.page.wait_for_timeout(200)
                logger.debug("Selected all sources")
            else:
                # Try text-based selector
                select_all_text = self.page.locator("text=Select all").first
                if await select_all_text.is_visible(timeout=3000):
                    await select_all_text.click()
                    await self.page.wait_for_timeout(200)
                    logger.debug("Selected all sources (via text)")
                else:
                    logger.warning("'Select all' option not found")

            # Import sources
            logger.debug("Looking for 'Import' button...")
            import_btn = self.page.locator("button").filter(
                has_text=re.compile(r"Import", re.I)
            ).first

            if await import_btn.is_visible(timeout=3000):
                await import_btn.click()
                logger.info("✓ Search sources imported successfully")
                await self.page.wait_for_timeout(2000)  # Wait for import processing
                return True
            else:
                logger.warning("Import button not visible")
                return False

        except Exception as e:
            logger.error(f"Error injecting search source: {e}")
            return False

    async def verify_sources_loaded(self) -> int:
        """
        Verify that sources have been loaded into the notebook.

        Returns:
            Number of sources loaded (0 if none detected)
        """
        logger.debug("Verifying sources loaded...")

        try:
            # Look for source indicators in the UI
            # This is approximate - NotebookLM UI varies
            source_indicators = await self.page.locator(
                "div[class*='source'], li[class*='source']"
            ).count()

            logger.info(f"Detected {source_indicators} source indicators")
            return source_indicators

        except Exception as e:
            logger.warning(f"Could not verify sources: {e}")
            return 0
