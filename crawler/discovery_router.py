from typing import List, Any
import logging
from contracts.source_policy import TRUSTED_DOMAINS, SourceType

logger = logging.getLogger(__name__)

async def discover_urls(page: Any, query: str, max_results: int = 10, method: str = "auto") -> List[str]:
    """
    Discover URLs based on the query and method with robust fallback logic.
    """
    method = method.lower()

    # Import scrapers locally to avoid circular dependencies or strict requirement if unused
    from discovery.google_scraper import scrape_google_search
    from discovery.ddg_scraper import scrape_ddg_search

    urls = []

    # Logic:
    # 1. Google requested: Google -> Fallback DDG
    # 2. DDG requested: DDG -> Fallback Google
    # 3. Auto: DDG -> Fallback Google

    primary_strategy = "ddg"
    if method == "google":
        primary_strategy = "google"

    logger.info(f"Starting discovery with strategy: {primary_strategy} (requested: {method})")

    try:
        if primary_strategy == "google":
            urls = await scrape_google_search(page, query, max_results=max_results)
        else:
            urls = await scrape_ddg_search(page, query, max_results=max_results)

    except Exception as e:
        logger.error(f"Primary discovery method '{primary_strategy}' failed: {e}")
        logger.info("Attempting fallback strategy...")

        try:
            # Fallback to the OTHER method
            if primary_strategy == "google":
                logger.info("Fallback: DDG")
                urls = await scrape_ddg_search(page, query, max_results=max_results)
            else:
                logger.info("Fallback: Google")
                # Fallback to Google requires a page object. If page is None (headless/api mode), we might fail again.
                if page:
                    urls = await scrape_google_search(page, query, max_results=max_results)
                else:
                    logger.warning("Cannot fallback to Google Search: No browser page available.")
        except Exception as e2:
             logger.error(f"Fallback discovery failed: {e2}")

    if not urls:
        logger.warning(f"Discovery returned 0 URLs for query: '{query}'")

    return urls

def filter_urls(urls: List[str], source_type) -> List[str]:
    """
    Filters URLs based on the source policy.
    - Trusted mode = hard allowlist
    - General mode = no filtering
    """
    # Normalize to string value
    if isinstance(source_type, SourceType):
        source_type = source_type.value
    
    if source_type == SourceType.TRUSTED.value:
        return [
            u for u in urls
            if any(domain in u for domain in TRUSTED_DOMAINS)
        ]
    return urls
