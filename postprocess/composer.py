from typing import Dict, Any
from contracts.output_schema import FinalOutput, OutputMetadata

def compose_output(ai_result: Dict[str, Any], output_type: str) -> Dict[str, Any]:
    """
    Composes the final output from AI results.

    Args:
        ai_result: The raw dictionary returned by the AI pipeline (DeepSeek/NotebookLM).
        output_type: The requested output format (e.g., 'study_material', 'quiz').

    Returns:
        A dictionary matching the FinalOutput schema.
    """
    # Extract summary or default
    summary = ai_result.get("summary", "")
    if not summary and "evidence" in ai_result:
        summary = "Generated from NotebookLM Evidence"

    # Create metadata
    metadata = OutputMetadata(
        output_type=output_type,
        ai_metadata={"raw_keys": list(ai_result.keys())}
    )

    # Construct final output object
    final_output = FinalOutput(
        summary=summary,
        metadata=metadata,
        format="json",
        content=ai_result
    )

    # Return as dict for serialization
    return final_output.model_dump()
