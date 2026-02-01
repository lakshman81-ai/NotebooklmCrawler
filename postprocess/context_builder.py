from contracts.content_request import ContentRequest

def build_context(request: ContentRequest) -> dict:
    """
    Extracts context from the request for AI prompting.
    This context is NOT used in crawling (stability), but in AI prompting + output shaping.
    """
    return {
        "grade": request.grade,
        "topic": request.topic,
        "subtopics": request.subtopics,
        "output_type": request.output_type,
        "custom_prompt": request.custom_prompt,
        "difficulty": request.difficulty,
        "keywords_report": request.keywords_report,
        "output_config": request.output_config,
        "local_file_path": request.local_file_path
    }
