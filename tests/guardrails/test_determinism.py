from postprocess.chunker import chunk_sections
from contracts.extraction_schema import ExtractedSection

def test_chunking_is_deterministic():
    sample_sections = [
        ExtractedSection(heading="H1", content="Content " * 100),
        ExtractedSection(heading="H2", content="Content " * 50)
    ]

    chunks_1 = chunk_sections(sample_sections)
    chunks_2 = chunk_sections(sample_sections)

    assert chunks_1 == chunks_2, \
        "Chunking is non-deterministic"
