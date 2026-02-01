"""TARGET_URL=https://byjus.com/ncert-solutions-class-8-science/chapter-11-force-and-pressure/
Orchestration Cockpit - Entry Point

Discovery Policy:
- Search engines (e.g., Google) are used ONLY for URL discovery.
- Discovered URLs MUST be cached in outputs/discovery/urls.json.
- Subsequent runs MUST reuse cached URLs unless cache is explicitly cleared.
- Live SERP scraping on every run is FORBIDDEN.

Execution Assumption:
- Script is executed from project root.
- All relative paths are resolved from project root.
- Do NOT change working directory at runtime.
"""

import os
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Force project root execution
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)

from logging_config import setup_logging  # noqa: E402
from crawler.browser import launch_browser  # noqa: E402
from crawler.navigation import fetch_page  # noqa: E402
from extractors.html_extractor import extract  # noqa: E402
from postprocess.cleaner import clean_html  # noqa: E402
from postprocess.chunker import chunk_sections  # noqa: E402
from contracts.content_request import ContentRequest  # noqa: E402
from crawler.discovery_router import filter_urls  # noqa: E402
from postprocess.context_builder import build_context  # noqa: E402
from outputs.composer import compose_output  # noqa: E402
from ai_pipeline.ai_router import run_ai  # noqa: E402

# Load env vars
load_dotenv(override=True)

# Setup logging
setup_logging()
logger = logging.getLogger("orchestrator")

# Constants
DISCOVERY_CACHE_PATH = Path("outputs/discovery/urls.json")
RAW_DIR = Path("outputs/html/raw")
CLEANED_DIR = Path("outputs/html/cleaned")
DOCX_DIR = Path("outputs/docx")
EXCEL_DIR = Path("outputs/excel")
FINAL_OUTPUT_DIR = Path("outputs/final")  # For .txt/.json results


def ensure_dirs():
    dirs = [
        "outputs/discovery",
        "outputs/html/raw",
        "outputs/html/cleaned",
        "outputs/docx",
        "outputs/excel",
        "outputs/final",
        "logs",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def get_content_request() -> ContentRequest:
    output_config_str = os.getenv("CR_OUTPUT_CONFIG", "{}")
    try:
        output_config = json.loads(output_config_str)
    except:
        output_config = {}

    return ContentRequest(
        grade=os.getenv("CR_GRADE", "Grade 8"),
        topic=os.getenv("CR_TOPIC", "Exponents"),
        subtopics=os.getenv("CR_SUBTOPICS", "laws,zero exponent").split(","),
        output_type=os.getenv("CR_OUTPUT_TYPE", "study_material"),
        custom_prompt=os.getenv("CR_CUSTOM_PROMPT", ""),
        source_type=os.getenv("CR_SOURCE_TYPE", "trusted"),
        difficulty=os.getenv("CR_DIFFICULTY", "Medium"),
        keywords_report=os.getenv("CR_KEYWORDS_REPORT", ""),
        output_config=output_config,
        local_file_path=os.getenv("CR_LOCAL_FILE_PATH", "")
    )


def get_target_urls() -> list:
    """
    Implements Discovery Policy.
    """
    if not DISCOVERY_CACHE_PATH.exists():
        # Should have been created by setup but good to be safe
        ensure_dirs()
        with open(DISCOVERY_CACHE_PATH, "w") as f:
            json.dump({"source": "manual", "last_updated": None, "urls": []}, f)

    with open(DISCOVERY_CACHE_PATH, "r") as f:
        cache = json.load(f)

    urls = cache.get("urls", [])

    # Check for override from Environment (e.g. fresh run from UI)
    env_target_url = os.getenv("TARGET_URL")
    if env_target_url:
        if "," in env_target_url:
            env_urls = [u.strip() for u in env_target_url.split(",") if u.strip()]
        else:
            env_urls = [env_target_url.strip()]
        
        # If env provided different URLs, overwrite cache
        if env_urls and env_urls != urls:
            logger.info(f"Target URL override detected. Old: {len(urls)}, New: {len(env_urls)}")
            urls = env_urls
            cache["urls"] = urls
            cache["last_updated"] = datetime.now().isoformat()
            cache["source"] = "env_target_url_override"
            with open(DISCOVERY_CACHE_PATH, "w") as f:
                json.dump(cache, f, indent=2)

    if not urls:
        logger.error("Discovery cache empty and TARGET_URL not set.")
        raise RuntimeError(
            "No URLs to process. Set TARGET_URL in .env or populate outputs/discovery/urls.json"
        )
    else:
        logger.info(f"Using {len(urls)} URLs from discovery cache")

    return urls


def save_raw(html: str, url: str, index: int):
    timestamp = datetime.now().isoformat()
    filename = f"page_{index:03d}.html"
    filepath = RAW_DIR / filename

    content = f"<!--\nURL: {url}\nFETCHED_AT: {timestamp}\n-->\n{html}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Saved raw HTML to {filepath}")
    return filepath


def save_cleaned(html: str, index: int):
    filename = f"page_{index:03d}.html"
    filepath = CLEANED_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    logger.info(f"Saved cleaned HTML to {filepath}")
    return filepath


def save_outputs(final_output: dict, index: int):
    # Save as JSON
    json_path = FINAL_OUTPUT_DIR / f"result_{index:03d}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    # Save as TXT
    txt_path = FINAL_OUTPUT_DIR / f"result_{index:03d}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Summary:\n{final_output.get('summary', '')}\n")

    # Stub DOCX/Excel
    docx_path = DOCX_DIR / f"result_{index:03d}.docx"
    with open(docx_path, "w") as f:
        f.write("NOT IMPLEMENTED")

    excel_path = EXCEL_DIR / f"result_{index:03d}.xlsx"
    with open(excel_path, "w") as f:
        f.write("NOT IMPLEMENTED")

    logger.info(f"Saved outputs to {FINAL_OUTPUT_DIR}")


async def collect_chunks_from_url(playwright, browser, browser_context, page, url: str, index: int) -> list:
    logger.info(f"Collecting chunks from [{index}] {url}")

    # 1. Fetch
    html = await fetch_page(page, url)

    # 2. Save Raw (Evidence)
    save_raw(html, url, index)

    # 3. Clean HTML
    cleaned_html = clean_html(html)

    # 4. Save Cleaned HTML
    save_cleaned(cleaned_html, index)

    # 5. Extract Title/Metadata from RAW HTML (for accuracy)
    doc_metadata = extract(html, url)
    
    # 6. Extract Sections/Content from CLEANED HTML
    doc_content = extract(cleaned_html, url)
    
    # Combine (Prioritize raw metadata)
    doc = doc_content
    doc.title = doc_metadata.title

    # 6. Chunk with Keyword Filtering
    chunking_strategy = os.getenv("CHUNKING_STRATEGY", "section_aware")
    # Fetch subtopics from env via a helper or direct
    subtopics_raw = os.getenv("CR_SUBTOPICS", "")
    keywords = [k.strip() for k in subtopics_raw.split(",") if k.strip()]
    
    chunks = chunk_sections(doc.sections, strategy=chunking_strategy, keywords=keywords, source_title=doc.title)
    
    if not chunks:
        logger.warning(f"No chunks produced for {url}")
        return []

    return chunks


async def main():
    ensure_dirs()

    discovery_method = os.getenv("DISCOVERY_METHOD", "auto").lower()
    request = get_content_request()
    logger.info(f"Content Request: {request} | Discovery: {discovery_method}")

    playwright = None
    browser = None
    context = None
    page = None

    try:
        logger.info("Initializing browser...")
        playwright, browser, context, page = await launch_browser()
        logger.info("Browser initialized successfully")

        ai_context = build_context(request)
        ai_context['discovery_method'] = discovery_method

        if discovery_method == "notebooklm":
            logger.info("Routing to NotebookLM Discovery Flow")
            ai_result = await run_ai([], ai_context, page)
        else:
            urls = get_target_urls()
            urls = filter_urls(urls, request.source_type)
            
            if not urls:
                logger.warning(f"No URLs remaining after filtering for source_type={request.source_type}")
                return

            all_chunks = []
            for i, url in enumerate(urls, 1):
                logger.info(f"Pipeline: Starting collection for URL {i}/{len(urls)}")
                chunks = await collect_chunks_from_url(playwright, browser, context, page, url, i)
                all_chunks.extend(chunks)
                logger.info(f"Pipeline: Finished collection for URL {i}/{len(urls)}")

            if not all_chunks:
                raise RuntimeError("No chunks collected from any URL — aborting AI pipeline")

            # 7. AI Pipeline (Unified Compilation)
            logger.info(f"Running AI Pipeline on {len(all_chunks)} aggregated chunks")
            ai_result = await run_ai(all_chunks, ai_context, page)

        # Assert contract
        assert isinstance(ai_result, dict)
        assert "summary" in ai_result or "evidence" in ai_result

        # Compose
        final_output = compose_output(ai_result, request.output_type)

        # 8. Save Outputs
        save_outputs(final_output, 0) # Use 0 for compiled output

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Closing browser resources")
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
