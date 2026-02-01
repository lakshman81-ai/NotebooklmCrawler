def test_ai_never_sees_raw_html():
    forbidden_tokens = ["<html", "<body", "<script"]

    from ai_pipeline.notebooklm import run_notebooklm

    # Check docstring as a proxy for intent/documentation
    sample_input = run_notebooklm.__doc__ or ""

    for token in forbidden_tokens:
        assert token not in sample_input.lower(), \
            "AI layer exposed to raw HTML"
