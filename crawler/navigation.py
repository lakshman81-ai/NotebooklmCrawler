import logging
import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

async def fetch_page(page, url: str, retries: int = 3) -> str:
    """
    Fetches a page content with strict timeout, stabilization, and retries.
    """
    logger.info(f"Navigating to {url} (Retries: {retries})")

    for attempt in range(retries):
        try:
            # 1. Navigation (Fastest Load)
            try:
                # 'domcontentloaded' is much faster than 'networkidle'
                # We use it to get initial HTML, then use smart waiting
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                logger.warning(f"Navigation timeout on {url} (Attempt {attempt+1})")
                if attempt == retries - 1: raise
                continue
            except Exception as e:
                logger.warning(f"Navigation error on {url}: {e}")
                if attempt == retries - 1: raise
                continue

            # 2. Smart Stabilization
            # Wait for BODY to be present (basic check)
            try:
                await page.wait_for_selector("body", timeout=5000)
            except:
                logger.warning("Body selector timeout. Page might be empty.")

            # Optional: Check for blocking/captcha
            content = await page.content()
            content_lower = content.lower()

            # Simple heuristics for blocks
            block_indicators = ["captcha", "access denied", "security check", "challenge-form", "cloudflare"]
            if len(content) < 500 or any(b in content_lower for b in block_indicators):
                if len(content) < 500:
                    logger.warning(f"Page content suspicious (Length: {len(content)}). Attempt {attempt+1}")
                else:
                    logger.warning(f"Potential block detected (Captcha/Security). Attempt {attempt+1}")

                # Exponential backoff
                await asyncio.sleep(2 * (attempt + 1))
                continue

            logger.info(f"Page content fetched successfully ({len(content)} bytes)")
            return content

        except Exception as e:
            logger.error(f"Failed to fetch page (Attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)
            else:
                raise

    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")
