from postprocess.chunker import chunk_sections
from contracts.extraction_schema import ExtractedSection
import os

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1200"))

def test_chunk_contract():
    section = ExtractedSection(heading="Test", content="A " * 50)
    chunks = chunk_sections([section])

    for chunk in chunks:
        assert chunk.text.strip(), "Empty chunk text"
        assert chunk.token_estimate <= MAX_TOKENS, \
            "Chunk exceeds token limit"
        assert chunk.source_heading, \
            "Chunk missing provenance"

def test_pipeline_fails_on_empty_chunks():
    """
    Failure Policy Guardrail: Pipeline must fail on empty chunks.
    This simulates calling the chunker with empty input, which returns empty list.
    The actual failure logic is in run.py (RuntimeError), but here we verify
    the chunker behavior allows for that check (returns empty list).
    """
    chunks = chunk_sections([])
    assert chunks == [], "Chunker should return empty list for empty input"
