import logging
import os
import uuid
from typing import Dict, List, Optional

import requests

from contracts.chunk_schema import Chunk
from prompt_modules.input_source_prompts import InputSourcePromptBuilder

logger = logging.getLogger(__name__)

# Modes
MODE_URL_DIRECT = "url_direct"
MODE_CHUNK_BASED = "chunk_based"


class AnythingLLMClient:
    """
    REST API client for a self-hosted AnythingLLM instance.

    Supports two ingestion modes:
      - url_direct:   Pass URLs directly → AnythingLLM scrapes them (no Playwright needed)
      - chunk_based:  Upload pre-crawled text chunks via raw-text endpoint
    """

    def __init__(self):
        self.base_url = os.getenv("ANYTHINGLLM_BASE_URL", "http://localhost:3001").rstrip("/")
        self.api_key = os.getenv("ANYTHINGLLM_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Workspace management
    # ------------------------------------------------------------------

    def create_workspace(self, name: str) -> str:
        """Create a temporary workspace. Returns the workspace slug."""
        resp = requests.post(
            f"{self.base_url}/api/v1/workspace/new",
            json={"name": name},
            headers=self.headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["workspace"]["slug"]

    def delete_workspace(self, slug: str):
        """Delete a workspace and all its embedded documents."""
        try:
            resp = requests.delete(
                f"{self.base_url}/api/v1/workspace/{slug}",
                headers=self.headers,
                timeout=15,
            )
            if resp.status_code not in (200, 204, 404):
                logger.warning(f"Unexpected status {resp.status_code} deleting workspace {slug}")
        except requests.RequestException as e:
            logger.warning(f"Could not delete workspace {slug}: {e}")

    def add_docs_to_workspace(self, slug: str, doc_locations: List[str]):
        """Embed a list of document paths into the workspace."""
        resp = requests.post(
            f"{self.base_url}/api/v1/workspace/{slug}/update-embeddings",
            json={"adds": doc_locations, "deletes": []},
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # Mode D1: URL-Direct ingestion
    # ------------------------------------------------------------------

    def upload_urls(self, urls: List[str]) -> List[str]:
        """
        Scrape each URL via AnythingLLM's collector and return the
        resulting document location paths (for add_docs_to_workspace).
        """
        doc_locations = []
        for url in urls:
            try:
                resp = requests.post(
                    f"{self.base_url}/api/v1/document/upload-link",
                    json={"link": url},
                    headers=self.headers,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                # AnythingLLM returns {"documents": [{"location": "..."}]}
                for doc in data.get("documents", []):
                    loc = doc.get("location")
                    if loc:
                        doc_locations.append(loc)
            except requests.RequestException as e:
                logger.warning(f"AnythingLLM failed to upload URL {url}: {e}")
        return doc_locations

    # ------------------------------------------------------------------
    # Mode D2: Chunk-Based ingestion
    # ------------------------------------------------------------------

    def upload_chunks(self, chunks: List[Chunk], session_id: str) -> List[str]:
        """
        Upload pre-crawled text chunks as raw text documents.
        Returns document location paths.
        """
        doc_locations = []
        for i, chunk in enumerate(chunks):
            title = f"[{chunk.source_title}] {chunk.source_heading}" if chunk.source_heading else chunk.source_title
            try:
                resp = requests.post(
                    f"{self.base_url}/api/v1/document/raw-text",
                    json={
                        "content": chunk.text,
                        "metadata": {
                            "title": title,
                            "docAuthor": "NotebooklmCrawler",
                            "description": f"Session {session_id} chunk {i}",
                        },
                    },
                    headers=self.headers,
                    timeout=15,
                )
                resp.raise_for_status()
                data = resp.json()
                for doc in data.get("documents", []):
                    loc = doc.get("location")
                    if loc:
                        doc_locations.append(loc)
            except requests.RequestException as e:
                logger.warning(f"AnythingLLM failed to upload chunk {i}: {e}")
        return doc_locations

    # ------------------------------------------------------------------
    # Chat / RAG query
    # ------------------------------------------------------------------

    def chat(self, slug: str, message: str) -> str:
        """Send a synthesis prompt to the workspace. Returns the response text."""
        resp = requests.post(
            f"{self.base_url}/api/v1/workspace/{slug}/chat",
            json={"message": message, "mode": "query"},
            headers=self.headers,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("textResponse", "")


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

def run_anythingllm(chunks: List[Chunk], context: Optional[Dict] = None) -> Dict:
    """
    Synthesize educational content using AnythingLLM's RAG pipeline.

    Selects the ingestion mode based on ANYTHINGLLM_MODE env var:
      - url_direct   (default): extract source URLs from chunk metadata,
                                pass them to AnythingLLM's collector
      - chunk_based:            upload pre-crawled text chunks as raw text

    CONTRACT:
    - Input:
        - chunks: List[Chunk]
        - context: Optional dict (grade, topic, subject, etc.)
    - Output: dict with keys:
        - summary: str
        - derived_from_chunks: List[int]
        - mode: str ("anythingllm_url_direct" | "anythingllm_chunk_based")
    """
    context = context or {}
    mode = os.getenv("ANYTHINGLLM_MODE", MODE_URL_DIRECT).lower()
    logger.info(f"Running AnythingLLM synthesis (mode={mode})")

    if not chunks:
        logger.warning("No chunks provided to AnythingLLM")
        return {"summary": "", "derived_from_chunks": [], "mode": f"anythingllm_{mode}"}

    # Build synthesis prompt (reuse same builder as NotebookLM / Khoj)
    prompt_builder = InputSourcePromptBuilder(
        grade=context.get("grade", "General"),
        subject=context.get("subject", "General"),
        topic=context.get("topic", ""),
        difficulty=context.get("difficulty", "Medium"),
        keywords=context.get("keywords", []),
    )
    prompt = prompt_builder.generate_notebooklm_prompt(
        context.get("output_config", {"studyGuide": True, "quiz": True}),
        context.get("custom_prompt", ""),
    )

    client = AnythingLLMClient()
    session_id = uuid.uuid4().hex[:12]
    workspace_name = f"nbc_session_{session_id}"
    slug = None

    try:
        slug = client.create_workspace(workspace_name)
        logger.info(f"AnythingLLM workspace created: {slug}")

        if mode == MODE_URL_DIRECT:
            doc_locations = _ingest_via_urls(client, chunks)
        else:
            doc_locations = client.upload_chunks(chunks, session_id)

        if not doc_locations:
            logger.warning("AnythingLLM: no documents ingested — running prompt without context")
        else:
            client.add_docs_to_workspace(slug, doc_locations)
            logger.info(f"AnythingLLM: {len(doc_locations)} docs embedded into workspace")

        summary = client.chat(slug, prompt)

    except requests.RequestException as e:
        raise RuntimeError(f"AnythingLLM pipeline failed: {e}") from e
    finally:
        if slug:
            client.delete_workspace(slug)
            logger.info(f"AnythingLLM workspace {slug} cleaned up")

    derived_chunk_ids = [c.chunk_id for c in chunks]
    logger.info(f"AnythingLLM synthesis complete ({len(chunks)} chunks → {len(summary)} chars)")

    return {
        "summary": summary,
        "derived_from_chunks": derived_chunk_ids,
        "mode": f"anythingllm_{mode}",
    }


def _ingest_via_urls(client: AnythingLLMClient, chunks: List[Chunk]) -> List[str]:
    """
    Extract unique source URLs from chunk metadata and upload them.
    Falls back to chunk-based upload if no URLs are found.
    """
    urls = []
    seen = set()
    for chunk in chunks:
        url = (
            chunk.metadata.get("url")
            or chunk.metadata.get("source_url")
            or chunk.metadata.get("link")
            or ""
        )
        if url and url not in seen:
            urls.append(url)
            seen.add(url)

    if urls:
        logger.info(f"AnythingLLM URL-Direct: uploading {len(urls)} unique URLs")
        return client.upload_urls(urls)

    # No URLs in metadata — fall back silently to chunk text upload
    logger.info("AnythingLLM URL-Direct: no source URLs found in metadata, falling back to raw-text upload")
    session_id = uuid.uuid4().hex[:8]
    return client.upload_chunks(chunks, session_id)
