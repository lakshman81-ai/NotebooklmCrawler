from pydantic import BaseModel, Field
from typing import List, Optional
from contracts.source_policy import SourceType

class ContentRequest(BaseModel):
    grade: str              # e.g. "Grade 8"
    topic: str              # e.g. "Exponents"
    subtopics: List[str]    # e.g. ["laws", "zero exponent"]
    output_type: str        # study_material | questionnaire | handout
    custom_prompt: str = "" # User-edited prompt
    # Deep Logic Fields
    difficulty: str = "Medium" # Identify, Connect, Extend
    keywords_report: str = ""
    output_config: dict = {} # { "studyGuide": true, "quiz": true, ... }
    local_file_path: str = ""
    source_type: SourceType # trusted | general

    # New fields for modular prompt system (Phase 4)
    output_formats: List[str] = Field(default_factory=lambda: ['markdown'])  # csv, pdf, html, docx, excel
    purpose: str = ""  # Learning objective description (e.g. "improve assertion reasoning", "clarify concept: mass vs weight")
    multi_report_types: List[str] = Field(default_factory=lambda: ['student'])  # student, teacher, admin
    quiz_config: dict = Field(default_factory=dict)  # { "mcq": 10, "ar": 5, "detailed": 3, "custom": "" }
    target_url: Optional[str] = None  # Optional URL for guided mode
