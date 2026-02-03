from typing import List, Any
from contracts.source_policy import TRUSTED_DOMAINS, SourceType

async def discover_urls(page: Any, query: str, max_results: int = 10, method: str = "auto") -> List[str]:
    """
    Discover URLs based on the query and method.
    """
    if method == "google":
        from discovery.google_scraper import scrape_google_search
        return await scrape_google_search(page, query, max_results=max_results)
    elif method == "ddg" or method == "auto":
        from discovery.ddg_scraper import scrape_ddg_search
        return await scrape_ddg_search(page, query, max_results=max_results)

    return []

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
