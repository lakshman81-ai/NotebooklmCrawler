import logging
from typing import Dict, List, Union, Optional
from contracts.chunk_schema import Chunk

logger = logging.getLogger(__name__)

def run_deepseek(input_data: Union[Dict, List[Chunk]], context: Optional[Dict] = None) -> Dict:
    """
    Mock implementation of DeepSeek.

    CONTRACT:
    - Input:
        - input_data: Dict (NotebookLM output) OR List[Chunk] (Fallback)
        - context: Optional context dict
    - Output: dict with keys:
        - summary: str
        - derived_from_chunks: List[int]
    """
    context_info = f" with context {context}" if context else ""
    logger.info(f"Running DeepSeek mock{context_info}")

    summary = ""
    derived_from_chunks = []

    if isinstance(input_data, dict):
        # Mode A: Evidence -> Synthesis
        logger.info("DeepSeek Mode A: Synthesis from Evidence")
        summary = "This is a mock synthesized summary derived from the evidence."
        derived_from_chunks = input_data.get("source_chunk_ids", [])

    elif isinstance(input_data, list):
        # Mode B: Direct Synthesis
        logger.info("DeepSeek Mode B: Direct Synthesis from Chunks")
        summary = "This is a mock direct synthesis derived from chunks (Fallback mode)."
        # Verify elements are chunks?
        if input_data and isinstance(input_data[0], Chunk):
            derived_from_chunks = [c.chunk_id for c in input_data]
        else:
            logger.warning("Input list does not contain Chunks?")
            derived_from_chunks = []
    else:
        raise ValueError(f"Invalid input type for DeepSeek: {type(input_data)}")

    result = {
        "summary": summary,
        "derived_from_chunks": derived_from_chunks
    }

    logger.info("DeepSeek mock completed")
    return result
