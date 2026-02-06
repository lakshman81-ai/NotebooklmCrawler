import pytest
from postprocess.composer import compose_output

def test_compose_output_study_material():
    """Test study material composition."""
    ai_result = {
        "summary": "Force is a push or pull. Pressure is force per unit area. This is a key point.",
        "evidence": ["Newton's laws", "Hydraulic principles"],
        "metadata": {"model": "gpt-4"},
        "sources": ["byjus.com"]
    }

    result = compose_output(ai_result, "study_material")

    assert result["summary"] == ai_result["summary"]
    assert result["format"] == "study_material"
    assert result["metadata"]["output_type"] == "study_material"
    assert result["metadata"]["ai_metadata"] == ai_result["metadata"]
    assert result["metadata"]["sources"] == ai_result["sources"]
    assert result["content"]["type"] == "study_material"
    assert len(result["content"]["key_points"]) > 0

def test_compose_output_missing_summary_uses_evidence():
    """Test fallback when summary is missing."""
    ai_result = {
        "evidence": ["First evidence item", "Second evidence item"]
    }

    result = compose_output(ai_result, "study_material")

    assert result["summary"] == "First evidence item"

def test_compose_output_invalid_type():
    """Test that invalid input raises TypeError."""
    with pytest.raises(TypeError):
        compose_output("not a dict", "study_material")

def test_compose_output_missing_required_keys():
    """Test that missing keys raises ValueError."""
    with pytest.raises(ValueError):
        compose_output({}, "study_material")  # No summary or evidence

def test_compose_output_unknown_type_uses_fallback():
    """Test graceful handling of unknown output types."""
    ai_result = {"summary": "Test content"}

    result = compose_output(ai_result, "unknown_type")

    assert result is not None
    assert result["format"] == "unknown_type"
    assert result["content"]["type"] == "generic"

def test_compose_output_questionnaire():
    ai_result = {"summary": "Quiz content"}
    result = compose_output(ai_result, "questionnaire")
    assert result["content"]["type"] == "questionnaire"

def test_compose_output_handout():
    ai_result = {"summary": "Handout content"}
    result = compose_output(ai_result, "handout")
    assert result["content"]["type"] == "handout"
