from ai_pipeline.deepseek import run_deepseek

def test_ai_output_contract():
    """
    Verifies that the AI layer output adheres to the strict shape contract.
    """
    # Mock input bundle expected by DeepSeek
    input_data = {"source_chunk_ids": [1, 2], "evidence": ["..."]}

    result = run_deepseek(input_data)

    assert isinstance(result, dict), "AI output must be a dict"
    assert "summary" in result, "AI output missing 'summary'"
    assert "derived_from_chunks" in result, "AI output missing 'derived_from_chunks'"
    assert isinstance(result["derived_from_chunks"], list), "'derived_from_chunks' must be a list"
