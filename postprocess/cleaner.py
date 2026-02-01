import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def clean_html(html: str) -> str:
    """
    Performs semantic hygiene on the HTML content.
    Removes <script>, <style>, <noscript> and navigation elements.
    """
    logger.info("Starting HTML cleaning")

    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, noscript
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Remove navigation noise (menus, footers)
    # This is a heuristic and might be adjusted based on target site
    for tag in soup(["nav", "footer", "header"]):
        tag.decompose()

    # Identify cookie banners? (Hard without specific selectors, skipping for generic)

    # Return string representation of the cleaned soup
    cleaned_html = str(soup)

    logger.info("HTML cleaning completed")
    return cleaned_html
