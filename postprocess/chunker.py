import logging
from typing import List
from contracts.chunk_schema import Chunk
from contracts.extraction_schema import ExtractedSection
import os

logger = logging.getLogger(__name__)

# Load MAX_TOKENS from env, default to 1200
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1200"))

def estimate_tokens(text: str) -> int:
    """
    Deterministic token estimation.
    Rule: len(text) // 4
    """
    return len(text) // 4

def chunk_sections(sections: List[ExtractedSection], strategy: str = "section_aware", keywords: List[str] = None, source_title: str = "Unknown") -> List[Chunk]:
    """
    Chunks extracted sections into blocks respecting MAX_TOKENS.
    If keywords are provided, only sections containing at least one keyword are kept.
    Strategy:
    - 'section_aware': Preserves section/block integrity. If a block fits, add it. If not, start new chunk.
    - 'fixed_size': Strictly enforces MAX_TOKENS by splitting text if necessary.
    """
    if keywords:
        # Normalize keywords for case-insensitive matching
        k_lower = [k.lower().strip() for k in keywords if k.strip()]
        if k_lower:
            filtered_sections = []
            for sec in sections:
                content_lower = (sec.heading + " " + sec.content).lower()
                if any(k in content_lower for k in k_lower):
                    filtered_sections.append(sec)
            sections = filtered_sections
            logger.info(f"Filtering enabled. Kept {len(sections)} sections matching keywords: {k_lower}")

    logger.info(f"Starting chunking with strategy='{strategy}' and MAX_TOKENS={MAX_TOKENS}")

    chunks = []
    chunk_id_counter = 1

    if strategy == "section_aware":
        current_chunk_text = ""
        current_heading = ""

        for sec in sections:
            block = f"{sec.heading}\n{sec.content}\n"
            block_tokens = estimate_tokens(block)

            current_tokens = estimate_tokens(current_chunk_text)

            if current_tokens + block_tokens > MAX_TOKENS:
                if current_chunk_text:
                    chunks.append(Chunk(
                        chunk_id=chunk_id_counter,
                        source_heading=current_heading if current_heading else "Unknown",
                        source_title=source_title,
                        text=current_chunk_text,
                        token_estimate=current_tokens
                    ))
                    chunk_id_counter += 1

                current_chunk_text = block
                current_heading = sec.heading
            else:
                if not current_chunk_text:
                    current_heading = sec.heading
                current_chunk_text += block

        if current_chunk_text:
            chunks.append(Chunk(
                chunk_id=chunk_id_counter,
                source_heading=current_heading if current_heading else "Unknown",
                source_title=source_title,
                text=current_chunk_text,
                token_estimate=estimate_tokens(current_chunk_text)
            ))

    elif strategy == "fixed_size":
        # Flatten all text with headers, then slice strictly
        # We lose mapping of heading to exact text if we just flatten.
        # But we need 'source_heading'.
        # Let's iterate and fill.

        current_chunk_text = ""
        current_heading = ""

        for sec in sections:
            block = f"{sec.heading}\n{sec.content}\n"

            remaining_block = block
            first_pass = True

            while remaining_block:
                if first_pass:
                    if not current_chunk_text:
                        current_heading = sec.heading
                    first_pass = False

                current_tokens = estimate_tokens(current_chunk_text)
                space_tokens = MAX_TOKENS - current_tokens
                space_chars = space_tokens * 4

                if space_chars <= 0:
                    # Chunk full
                    chunks.append(Chunk(
                        chunk_id=chunk_id_counter,
                        source_heading=current_heading if current_heading else "Unknown",
                        text=current_chunk_text,
                        token_estimate=current_tokens
                    ))
                    chunk_id_counter += 1
                    current_chunk_text = ""
                    current_heading = sec.heading # Next chunk starts in this section
                    continue

                part = remaining_block[:space_chars]
                current_chunk_text += part
                remaining_block = remaining_block[space_chars:]

        if current_chunk_text:
             chunks.append(Chunk(
                chunk_id=chunk_id_counter,
                source_heading=current_heading if current_heading else "Unknown",
                source_title=source_title,
                text=current_chunk_text,
                token_estimate=estimate_tokens(current_chunk_text)
            ))

    else:
        logger.warning(f"Unknown strategy '{strategy}', defaulting to section_aware")
        return chunk_sections(sections, "section_aware")

    logger.info(f"Created {len(chunks)} chunks")
    return chunks
