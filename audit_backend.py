import sys
import os
import logging

# Mock logger
logging.basicConfig(level=logging.INFO)

# Add repo root to path so we can import prompt_modules
sys.path.append(os.getcwd())

from prompt_modules.input_source_prompts import InputSourcePromptBuilder
from prompt_modules.output_type_prompts import QuizPromptBuilder, StudyGuidePromptBuilder, HandoutPromptBuilder

def audit_backend():
    print("=== AUDITING BACKEND PROMPTS ===\n")

    # TEST CASE 1: Input Source Prompts (Search Queries)
    print("--- TEST CASE 1: Input Source Prompts ---")
    builder = InputSourcePromptBuilder(
        grade="Grade 8",
        subject="Physics",
        topic="Gravity",
        difficulty="Medium",
        keywords=["mass vs weight", "microgravity"]
    )

    print("Textbook Search:", builder.generate_textbook_search())
    print("Conceptual Search:", builder.generate_conceptual_search())
    print("Application Search:", builder.generate_application_search())
    print("Misconception Search:", builder.generate_misconception_search())
    print("Strategy:", builder.generate_multi_source_strategy())
    print("\n------------------------------------------------\n")

    # TEST CASE 2: Quiz Prompts
    print("--- TEST CASE 2: Quiz Prompts ---")
    quiz_config = {"mcq": 5, "ar": 2, "detailed": 1, "custom": "No negative marking"}
    quiz_builder = QuizPromptBuilder(
        quiz_config=quiz_config,
        difficulty="Medium",
        grade="Grade 8",
        keywords_report=["mass", "weight"]
    )
    print("Strict CSV Prompt:\n", quiz_builder.generate_strict_csv_prompt())
    print("\nAR Prompt:\n", quiz_builder.generate_assertion_reasoning_prompt())
    print("\n------------------------------------------------\n")

    # TEST CASE 3: Study Guide Prompts
    print("--- TEST CASE 3: Study Guide Prompts ---")
    guide_builder = StudyGuidePromptBuilder(
        keywords_report=["mass", "weight", "force"],
        difficulty="Medium",
        grade="Grade 8",
        page_count=3
    )
    print("Narrative Prompt:\n", guide_builder.generate_curriculum_narrative_prompt())
    print("\nComparison Table Prompt:\n", guide_builder.generate_comparison_table_prompt("Mass", "Weight"))
    print("\n------------------------------------------------\n")

    # TEST CASE 4: Handout Prompts
    print("--- TEST CASE 4: Handout Prompts ---")
    handout_builder = HandoutPromptBuilder(
        topic="Gravity",
        grade="Grade 8",
        keywords=["forces"]
    )
    print("LaTeX Prompt:\n", handout_builder.generate_latex_equation_prompt())
    print("\nMermaid Flowchart:\n", handout_builder.generate_mermaid_flowchart_prompt("gravity causes orbit"))
    print("\nDiagram Description:\n", handout_builder.generate_diagram_description_prompt())
    print("\n------------------------------------------------\n")

    # TEST CASE 5: URL Metadata Extraction
    print("--- TEST CASE 5: URL Metadata Extraction ---")
    print(builder.generate_url_metadata_extraction_prompt("https://www.khanacademy.org/science/physics"))
    print("\n------------------------------------------------\n")

if __name__ == "__main__":
    audit_backend()
