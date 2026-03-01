import io
import logging
import os
import uuid
from typing import Dict, List, Optional

import requests

from contracts.chunk_schema import Chunk
from prompt_modules.input_source_prompts import InputSourcePromptBuilder

logger = logging.getLogger(__name__)


class KhojClient:
    """
    REST API client for a self-hosted or cloud Khoj instance.
    Handles content upload, chat-based synthesis, and cleanup.
    """

    def __init__(self):
        self.base_url = os.getenv("KHOJ_BASE_URL", "http://localhost:42110").rstrip("/")
        self.api_key = os.getenv("KHOJ_API_KEY", "")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def upload_chunks(self, chunks: List[Chunk], session_id: str) -> List[str]:
        """
        Upload chunks as text files to Khoj via PATCH /api/content.
        Returns list of filenames used (for cleanup).
        """
        filenames = []
        files = []

        for i, chunk in enumerate(chunks):
            filename = f"khoj_{session_id}_chunk_{i}.txt"
            content = f"# {chunk.source_title}\n\n{chunk.text}"
            files.append(
                ("files", (filename, io.BytesIO(content.encode("utf-8")), "text/plain"))
            )
            filenames.append(filename)

        try:
            resp = requests.patch(
                f"{self.base_url}/api/content",
                files=files,
                headers=self.headers,
                timeout=30,
            )
            resp.raise_for_status()
            logger.info(f"Uploaded {len(filenames)} chunks to Khoj (session={session_id})")
        except requests.RequestException as e:
            logger.error(f"Khoj upload failed: {e}")
            raise RuntimeError(f"Khoj content upload failed: {e}") from e

        return filenames

    def query(self, prompt: str) -> str:
        """
        Send a synthesis prompt to Khoj via POST /api/chat.
        Returns the response text.
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"q": prompt, "stream": False},
                headers=self.headers,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", data.get("message", ""))
        except requests.RequestException as e:
            logger.error(f"Khoj chat query failed: {e}")
            raise RuntimeError(f"Khoj chat query failed: {e}") from e

    def cleanup(self, filenames: List[str]):
        """
        Delete uploaded chunk files from Khoj after synthesis is complete.
        """
        for filename in filenames:
            try:
                resp = requests.delete(
                    f"{self.base_url}/api/content/file",
                    params={"filename": filename},
                    headers=self.headers,
                    timeout=10,
                )
                if resp.status_code not in (200, 204, 404):
                    logger.warning(f"Unexpected status {resp.status_code} deleting {filename}")
            except requests.RequestException as e:
                logger.warning(f"Could not delete {filename} from Khoj: {e}")


def run_khoj(input_data: List[Chunk], context: Optional[Dict] = None) -> Dict:
    """
    Synthesize educational content using Khoj's RAG pipeline.

    CONTRACT:
    - Input:
        - input_data: List[Chunk]
        - context: Optional context dict (grade, topic, subject, etc.)
    - Output: dict with keys:
        - summary: str
        - derived_from_chunks: List[int]
        - mode: str ("khoj")
    """
    context = context or {}
    logger.info("Running Khoj synthesis")

    if not input_data:
        logger.warning("No chunks provided to Khoj")
        return {"summary": "", "derived_from_chunks": [], "mode": "khoj"}

    # Build synthesis prompt (reuse the same builder as NotebookLM)
    grade = context.get("grade", "General")
    subject = context.get("subject", "General")
    topic = context.get("topic", "")
    difficulty = context.get("difficulty", "Medium")
    keywords = context.get("keywords", [])
    output_config = context.get("output_config", {"studyGuide": True, "quiz": True})
    custom_prompt = context.get("custom_prompt", "")

    prompt_builder = InputSourcePromptBuilder(
        grade=grade,
        subject=subject,
        topic=topic,
        difficulty=difficulty,
        keywords=keywords,
    )
    prompt = prompt_builder.generate_notebooklm_prompt(output_config, custom_prompt)

    # Run Khoj pipeline: upload → query → cleanup
    client = KhojClient()
    session_id = uuid.uuid4().hex[:12]
    filenames = []

    try:
        filenames = client.upload_chunks(input_data, session_id)
        summary = client.query(prompt)
    finally:
        if filenames:
            client.cleanup(filenames)

    derived_chunk_ids = [c.chunk_id for c in input_data]
    logger.info(f"Khoj synthesis complete ({len(input_data)} chunks → {len(summary)} chars)")

    return {
        "summary": summary,
        "derived_from_chunks": derived_chunk_ids,
        "mode": "khoj",
    }
