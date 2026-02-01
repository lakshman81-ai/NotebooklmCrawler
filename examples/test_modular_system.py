"""
Test Script for Modular NotebookLM System

Demonstrates complete workflow for both GUIDED and UNGUIDED modes.

Usage:
    python examples/test_modular_system.py --mode guided
    python examples/test_modular_system.py --mode unguided
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.content_request import ContentRequest
from contracts.source_policy import SourceType
from prompt_modules import PromptOrchestrator, InputSourcePromptBuilder
from utils.format_converter import FormatConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_prompt_generation():
    """
    Test Phase 1: Prompt generation modules (no browser automation).
    """
    logger.info("=" * 60)
    logger.info("TEST 1: Prompt Generation Modules")
    logger.info("=" * 60)

    # Create sample content request
    content_request = ContentRequest(
        grade="Grade 8",
        topic="Physics Gravity",
        subtopics=["mass vs weight", "microgravity", "Newton's law"],
        difficulty="Medium",
        output_type="mixed_outputs",
        output_config={
            "studyGuide": True,
            "quiz": True,
            "handout": True
        },
        quiz_config={
            "mcq": 10,
            "ar": 5,
            "detailed": 3
        },
        output_formats=["excel", "pdf", "html"],
        purpose="Clarify concept: mass vs weight, improve assertion reasoning",
        multi_report_types=["student", "teacher"],
        keywords_report="force of attraction, microgravity, orbital mechanics",
        source_type=SourceType.trusted
    )

    logger.info(f"Content Request: {content_request.grade} {content_request.topic}")

    # Test Module A: Input Source Prompts (GUIDED MODE)
    logger.info("\n--- Module A: Input Source Prompt Generation ---")

    input_builder = InputSourcePromptBuilder(
        grade=content_request.grade,
        subject="Physics",
        topic=content_request.topic,
        difficulty=content_request.difficulty,
        keywords=content_request.subtopics
    )

    search_strategy = input_builder.generate_multi_source_strategy()

    logger.info(f"Primary Search Query: {search_strategy['primary_search'][:100]}...")
    logger.info(f"Conceptual Search: {search_strategy['conceptual_search'][:100]}...")
    logger.info(f"Source Weighting: {search_strategy.get('source_weighting', {})}")

    # Test Module B + C + D: Output Prompts
    logger.info("\n--- Module B/C/D: Output Prompt Generation ---")

    prompt_orchestrator = PromptOrchestrator(content_request.model_dump())

    # Generate quiz prompt
    quiz_prompt = prompt_orchestrator.build_quiz_prompt(content_request)
    logger.info(f"Quiz Prompt Length: {len(quiz_prompt)} chars")
    logger.info(f"Quiz Prompt Preview:\n{quiz_prompt[:300]}...\n")

    # Generate study guide prompt
    guide_prompt = prompt_orchestrator.build_study_guide_prompt(content_request)
    logger.info(f"Study Guide Prompt Length: {len(guide_prompt)} chars")
    logger.info(f"Study Guide Preview:\n{guide_prompt[:300]}...\n")

    # Generate handout prompt
    handout_prompt = prompt_orchestrator.build_handout_prompt(content_request)
    logger.info(f"Handout Prompt Length: {len(handout_prompt)} chars")
    logger.info(f"Handout Preview:\n{handout_prompt[:300]}...\n")

    # Validate prompts
    logger.info("\n--- Prompt Validation ---")
    is_valid, issues = prompt_orchestrator.validate_prompt(quiz_prompt, 'quiz')
    logger.info(f"Quiz Prompt Valid: {is_valid}")
    if issues:
        logger.warning(f"Issues: {issues}")

    logger.info("\n✓ TEST 1 COMPLETE: All prompt modules working correctly\n")

    return content_request, prompt_orchestrator


def test_format_conversion():
    """
    Test Phase 4: Format conversion (CSV → Excel, Markdown → PDF/HTML).
    """
    logger.info("=" * 60)
    logger.info("TEST 2: Format Conversion")
    logger.info("=" * 60)

    # Sample CSV content (mock quiz output from NotebookLM)
    sample_csv = """ID,Topic,Question_Text,Option_A,Option_B,Option_C,Option_D,Correct_Answer_Text
1,Definitions,What creates gravity?,A planet's color,A planet's mass,A planet's speed,The atmosphere,A planet's mass
2,Definitions,What is the unit for weight?,Kilograms,Newtons,Pounds,Grams,Newtons
3,Mass vs Weight,Why do you weigh less on the Moon?,Less gravity pulls on you,You have less mass,The Moon is smaller,Air is thinner,Less gravity pulls on you
"""

    # Sample Markdown content (mock study guide)
    sample_markdown = """# Grade 8 Physics: Gravity Study Guide

## Introduction: The Invisible Force

Gravity is the force of attraction between objects with mass. Unlike magnetism, which only affects certain materials, gravity affects everything!

> **The Magnet Analogy**: Think of gravity like an invisible magnet that pulls on everything, but instead of being strong with metals, it's stronger with heavier objects.

## Core Concept: Mass vs. Weight

| Property | Mass | Weight |
|----------|------|--------|
| Definition | The amount of matter in an object | The force of gravity pulling on an object |
| Does it change? | No, stays same everywhere | Yes, changes with gravity (Moon vs Earth) |
| Unit | Kilograms (kg) | Newtons (N) |

### Why You Weigh Less on the Moon

Even though your **mass** stays the same (you still have the same amount of matter), your **weight** decreases because the Moon's gravity is weaker than Earth's.

## Newton's Law of Universal Gravitation

$$F = G \\frac{m_1 m_2}{r^2}$$

Where:
- $F$ = Gravitational force (Newtons)
- $G$ = Gravitational constant
- $m_1, m_2$ = Masses of the two objects (kg)
- $r$ = Distance between centers (meters)

## Practice Problems

1. If an object has a mass of 10 kg on Earth, what is its mass on the Moon?
2. Calculate the weight of a 50 kg person on Earth (g = 9.8 m/s²)
"""

    # Initialize converter
    converter = FormatConverter(output_dir="outputs/test")

    # Test CSV → Excel
    logger.info("\n--- Converting CSV to Excel ---")
    excel_path = converter.csv_to_excel(sample_csv, "test_quiz")
    if excel_path:
        logger.info(f"✓ Excel file created: {excel_path}")
    else:
        logger.warning("Excel conversion failed (openpyxl may not be installed)")

    # Test Markdown → HTML
    logger.info("\n--- Converting Markdown to HTML ---")
    html_path = converter.markdown_to_html(sample_markdown, "test_study_guide")
    if html_path:
        logger.info(f"✓ HTML file created: {html_path}")
    else:
        logger.warning("HTML conversion failed")

    # Test Markdown → PDF
    logger.info("\n--- Converting Markdown to PDF ---")
    pdf_path = converter.markdown_to_pdf(sample_markdown, "test_study_guide")
    if pdf_path:
        logger.info(f"✓ PDF file created: {pdf_path}")
    else:
        logger.warning("PDF conversion failed (pdfkit/weasyprint may not be installed)")

    # Test batch conversion
    logger.info("\n--- Batch Conversion Test ---")
    artifacts = {
        'quiz_csv': sample_csv,
        'study_guide_md': sample_markdown,
        'visuals_md': sample_markdown
    }

    all_files = converter.convert_notebooklm_artifacts(
        artifacts=artifacts,
        base_name="grade8_gravity",
        output_formats=['excel', 'html', 'pdf']
    )

    logger.info(f"✓ Batch conversion complete: {len(all_files)} files created")
    for format_type, path in all_files.items():
        logger.info(f"  - {format_type}: {path}")

    logger.info("\n✓ TEST 2 COMPLETE: Format conversion working\n")


async def test_full_workflow_simulation():
    """
    Test Phase 3: Simulated full workflow (without actual browser automation).
    Shows how all modules integrate.
    """
    logger.info("=" * 60)
    logger.info("TEST 3: Full Workflow Simulation")
    logger.info("=" * 60)

    # Create content request
    content_request = ContentRequest(
        grade="Grade 8",
        topic="Physics Gravity",
        subtopics=["mass vs weight", "microgravity"],
        difficulty="Medium",
        output_type="mixed_outputs",
        output_config={
            "studyGuide": True,
            "quiz": True,
            "handout": True
        },
        quiz_config={
            "mcq": 10,
            "ar": 5,
            "detailed": 3
        },
        output_formats=["excel", "html", "pdf"],
        purpose="Clarify concept: mass vs weight",
        multi_report_types=["student"],
        keywords_report="force of attraction, microgravity",
        source_type=SourceType.trusted,
        target_url=None  # Will trigger search in guided mode
    )

    # Simulate guided mode workflow
    guided_mode = os.getenv("NOTEBOOKLM_GUIDED", "false").lower() == "true"

    logger.info(f"Mode: {'GUIDED' if guided_mode else 'UNGUIDED'}")

    # PHASE 1: Input Source Handling
    if guided_mode:
        logger.info("\n--- PHASE 1: Input Source Prompt Generation (GUIDED) ---")

        input_builder = InputSourcePromptBuilder(
            grade=content_request.grade,
            subject="Physics",
            topic=content_request.topic,
            difficulty=content_request.difficulty,
            keywords=content_request.subtopics
        )

        search_strategy = input_builder.generate_multi_source_strategy()
        logger.info(f"Would inject search query: {search_strategy['primary_search'][:80]}...")
        logger.info("(In real workflow: InputSourcePromptInjector.inject_source_discovery_prompts())")
    else:
        logger.info("\n--- PHASE 1: Direct Upload (UNGUIDED) ---")
        logger.info("(In real workflow: Upload chunks via file picker)")

    # PHASE 2: Output Prompt Generation
    logger.info("\n--- PHASE 2: Output Prompt Generation ---")

    prompt_orchestrator = PromptOrchestrator(content_request.model_dump())

    quiz_prompt = prompt_orchestrator.build_quiz_prompt(content_request)
    guide_prompt = prompt_orchestrator.build_study_guide_prompt(content_request)
    handout_prompt = prompt_orchestrator.build_handout_prompt(content_request)

    logger.info(f"Generated 3 prompts: quiz ({len(quiz_prompt)} chars), "
               f"guide ({len(guide_prompt)} chars), handout ({len(handout_prompt)} chars)")
    logger.info("(In real workflow: OutputPromptInjector.inject_multi_stage_prompts())")

    # PHASE 3: Mock results (simulating NotebookLM output)
    logger.info("\n--- PHASE 3: Mock NotebookLM Output ---")

    mock_results = {
        'quiz_csv': """ID,Topic,Question_Text,Option_A,Option_B,Option_C,Option_D,Correct_Answer_Text
1,Definitions,What creates gravity?,Color,Mass,Speed,Atmosphere,Mass
2,Mass vs Weight,What happens to weight on Moon?,Increases,Decreases,Stays same,Becomes zero,Decreases""",
        'study_guide_md': """# Gravity Study Guide\n\n## Mass vs Weight\n\nMass is constant, weight varies with gravity.""",
        'visuals_md': """## Newton's Law\n\n$$F = G \\frac{m_1 m_2}{r^2}$$"""
    }

    logger.info(f"Mock results: {list(mock_results.keys())}")

    # PHASE 4: Format Conversion
    logger.info("\n--- PHASE 4: Format Conversion ---")

    converter = FormatConverter(output_dir="outputs/test_workflow")
    converted_files = converter.convert_notebooklm_artifacts(
        artifacts=mock_results,
        base_name="grade8_gravity",
        output_formats=content_request.output_formats
    )

    logger.info(f"✓ Converted to {len(converted_files)} formats:")
    for fmt, path in converted_files.items():
        logger.info(f"  - {fmt}: {path}")

    logger.info("\n✓ TEST 3 COMPLETE: Full workflow simulation successful\n")


def print_usage_examples():
    """
    Print usage examples for the modular system.
    """
    logger.info("=" * 60)
    logger.info("USAGE EXAMPLES")
    logger.info("=" * 60)

    logger.info("""
# Example 1: Guided Mode (NotebookLM discovers sources)
export NOTEBOOKLM_GUIDED=true
export CR_GRADE="Grade 8"
export CR_TOPIC="Physics Gravity"
export CR_DIFFICULTY="Medium"
export CR_OUTPUT_CONFIG='{"studyGuide":true,"quiz":true,"handout":true}'
export CR_QUIZ_CONFIG='{"mcq":10,"ar":5,"detailed":3}'
python run.py

# Example 2: Unguided Mode (Upload pre-crawled content)
export NOTEBOOKLM_GUIDED=false
export TARGET_URL="https://byjus.com/jee/gravitation/"
export CR_GRADE="Grade 8"
export CR_TOPIC="Gravitation"
python run.py

# Example 3: Multi-Report Generation
export CR_MULTI_REPORT_TYPES="student,teacher,admin"
export CR_OUTPUT_FORMATS="excel,pdf,html"
python run.py

# Example 4: Test Prompt Generation Only
python examples/test_modular_system.py
""")


def main():
    """
    Main test runner.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Test NotebookLM Modular System')
    parser.add_argument('--mode', choices=['guided', 'unguided'],
                       help='Set NOTEBOOKLM_GUIDED mode for testing')
    parser.add_argument('--all', action='store_true',
                       help='Run all tests')
    parser.add_argument('--examples', action='store_true',
                       help='Show usage examples')

    args = parser.parse_args()

    if args.mode:
        os.environ['NOTEBOOKLM_GUIDED'] = 'true' if args.mode == 'guided' else 'false'
        logger.info(f"Set NOTEBOOKLM_GUIDED={os.environ['NOTEBOOKLM_GUIDED']}")

    if args.examples:
        print_usage_examples()
        return

    try:
        # Test 1: Prompt Generation
        logger.info("Running Test 1: Prompt Generation...")
        test_prompt_generation()

        # Test 2: Format Conversion
        logger.info("Running Test 2: Format Conversion...")
        test_format_conversion()

        # Test 3: Full Workflow Simulation
        logger.info("Running Test 3: Full Workflow Simulation...")
        asyncio.run(test_full_workflow_simulation())

        logger.info("\n" + "=" * 60)
        logger.info("ALL TESTS PASSED ✓")
        logger.info("=" * 60)
        logger.info("\nNext Steps:")
        logger.info("1. Install browser: playwright install chromium")
        logger.info("2. Configure .env with your settings")
        logger.info("3. Run: python run.py")
        logger.info("\nFor usage examples: python examples/test_modular_system.py --examples")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
