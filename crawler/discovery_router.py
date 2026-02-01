from typing import List
from contracts.source_policy import TRUSTED_DOMAINS, SourceType

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
