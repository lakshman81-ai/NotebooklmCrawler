import logging

logger = logging.getLogger(__name__)

async def fetch_page(page, url: str) -> str:
    """
    Fetches a page content with strict timeout and stabilization.
    """
    logger.info(f"Navigating to {url}")

    # 60 seconds timeout (fail hard policy)
    timeout_ms = 60000

    try:
        # Relaxed navigation: domcontentloaded is enough for "DOM style"
        logger.info(f"Triggering page.goto for {url}")
        await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        
        logger.info("DOM Content Loaded. Waiting for stabilization...")
        # Brief stabilization to let dynamic components settle
        await page.wait_for_timeout(2000)
        
        content = await page.content()
        logger.info(f"Page content fetched successfully ({len(content)} bytes)")
        return content
    except Exception as e:
        logger.error(f"Failed to fetch page: {e}")
        raise
