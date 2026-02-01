import logging
from bs4 import BeautifulSoup
from contracts.extraction_schema import ExtractedDocument

logger = logging.getLogger(__name__)

def extract(html: str, url: str) -> ExtractedDocument:
    logger.info(f"Starting Robust HTML extraction for {url}")

    soup = BeautifulSoup(html, "html.parser")
    
    # Robust title extraction
    title = ""
    # 1. Try OG Title
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
        
    # 2. Try standard title
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    
    # 3. Fallback to H1
    generic_titles = ["untitled", "document", "page", "home", "index"]
    if not title or title.lower() in generic_titles:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
            
    if not title:
        title = "Untitled Artifact"

    # 1. Identify "Main" container (Heuristic-based)
    # We look for common content containers
    main_content = soup.find(["article", "main", "div#content", "div.post-content", "div.article-content"])
    if not main_content:
        # Fallback to body if no obvious main container found
        main_content = soup.body if soup.body else soup

    sections = []
    
    # Standardize content: extract text from headers, paragraphs, lists, and tables
    # We navigate through children of the main container
    
    current_section = {"heading": "General", "content": []}
    
    # Select all potential content-bearing Tags
    items = main_content.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"])
    
    for item in items:
        # If it's a header, it starts a new section
        if item.name.startswith("h"):
            # Save previous section if it has content
            if current_section["content"]:
                sections.append({
                    "heading": current_section["heading"],
                    "content": " ".join(current_section["content"])
                })
            
            # Start new section
            current_section = {
                "heading": item.get_text(strip=True),
                "content": []
            }
        else:
            # It's content (p, li, table)
            text = item.get_text(" ", strip=True)
            if text:
                current_section["content"].append(text)

    # Final section
    if current_section["content"]:
        sections.append({
            "heading": current_section["heading"],
            "content": " ".join(current_section["content"])
        })

    doc = ExtractedDocument(
        title=title,
        sections=sections,
        source_url=url
    )

    logger.info(f"Robustly extracted {len(sections)} sections from document: {title}")
    return doc
