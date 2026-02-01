"""
Prompt Modules Package

Central orchestrator for all prompt generation modules.
Coordinates InputSourcePromptBuilder, OutputTypePromptBuilder, DifficultyEngine, and OutputFormatAdapter.
"""

import logging
from typing import Dict, Optional, List

from .input_source_prompts import InputSourcePromptBuilder
from .output_type_prompts import QuizPromptBuilder, StudyGuidePromptBuilder, HandoutPromptBuilder
from .difficulty_engine import DifficultyEngine
from .format_adapter import OutputFormatAdapter

logger = logging.getLogger(__name__)


class PromptOrchestrator:
    """
    Central coordinator for all prompt generation.

    Orchestrates:
        - Module A: InputSourcePromptBuilder (search queries)
        - Module B: OutputTypePromptBuilder (quiz/study/handout)
        - Module C: OutputFormatAdapter (format constraints)
        - Module D: DifficultyEngine (Bloom's taxonomy)
    """

    def __init__(self, context: Dict):
        """
        Initialize the prompt orchestrator with context from ContentRequest.

        Args:
            context: Dictionary with keys:
                - grade: str
                - topic: str
                - subtopics: List[str]
                - difficulty: str
                - output_config: dict
                - quiz_config: dict
                - output_formats: List[str] (optional)
                - purpose: str (optional)
                - keywords_report: str (optional)
        """
        self.context = context

        # Extract core parameters
        self.grade = context.get('grade', 'General')
        self.topic = context.get('topic', '')
        self.subtopics = context.get('subtopics', [])
        self.difficulty = context.get('difficulty', 'Medium')
        self.output_config = context.get('output_config', {})
        self.quiz_config = context.get('quiz_config', {})
        self.purpose = context.get('purpose', '')

        # Extract keywords for report generation
        keywords_report = context.get('keywords_report', '')
        self.keywords = self._parse_keywords(keywords_report, self.subtopics)

        # Extract subject from topic (first word typically)
        self.subject = self._extract_subject(self.topic)

        # Initialize sub-modules
        self.difficulty_engine = DifficultyEngine()

        self.format_adapter = OutputFormatAdapter({
            'formats': context.get('output_formats', ['markdown'])
        })

        logger.info(f"PromptOrchestrator initialized for {self.grade} {self.subject} - {self.topic}")

    def _parse_keywords(self, keywords_report: str, subtopics: List) -> List[str]:
        """
        Parse keywords from either keywords_report string or subtopics list.

        Args:
            keywords_report: Comma-separated keyword string
            subtopics: List of subtopic strings

        Returns:
            Unified list of keywords
        """
        keywords = []

        # Parse keywords_report
        if keywords_report:
            keywords.extend([k.strip() for k in keywords_report.split(',') if k.strip()])

        # Add subtopics
        if subtopics and isinstance(subtopics, list):
            keywords.extend(subtopics)
        elif subtopics and isinstance(subtopics, str):
            # Handle case where subtopics is still a string
            keywords.extend([s.strip() for s in subtopics.split(',') if s.strip()])

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k.lower() not in seen:
                seen.add(k.lower())
                unique_keywords.append(k)

        return unique_keywords

    def _extract_subject(self, topic: str) -> str:
        """
        Extract subject from topic string.

        Examples:
            "Physics Gravity" → "Physics"
            "Gravity" → "General"
        """
        # Common subjects
        subjects = ["Physics", "Chemistry", "Biology", "Math", "Science", "History", "English"]

        for subject in subjects:
            if subject.lower() in topic.lower():
                return subject

        # Default to General
        return "General"

    def build_quiz_prompt(self, content_request) -> str:
        """
        Build complete quiz prompt with all constraints.

        Args:
            content_request: ContentRequest object (or dict)

        Returns:
            Complete prompt string for quiz generation
        """
        logger.info("Building quiz prompt...")

        # Initialize quiz builder
        quiz_builder = QuizPromptBuilder(
            quiz_config=self.quiz_config,
            difficulty=self.difficulty,
            grade=self.grade,
            keywords_report=self.keywords
        )

        # Generate base quiz prompt
        base_prompt = quiz_builder.generate_strict_csv_prompt()

        # Add difficulty constraints
        difficulty_constraints = self.difficulty_engine.generate_difficulty_constraints(
            difficulty=self.difficulty,
            purpose=self.purpose
        )

        # Insert difficulty constraints after first line
        lines = base_prompt.split('\n')
        lines.insert(2, '\n' + difficulty_constraints + '\n')
        base_prompt = '\n'.join(lines)

        # Add format constraints (CSV)
        enhanced_prompt = self.format_adapter.inject_format_rules(base_prompt, 'csv')

        # Add negative constraints
        final_prompt = self.format_adapter.add_negative_constraints(enhanced_prompt, 'csv')

        logger.info(f"Quiz prompt built: {len(final_prompt)} chars")
        return final_prompt

    def build_study_guide_prompt(self, content_request) -> str:
        """
        Build complete study guide prompt.

        Args:
            content_request: ContentRequest object (or dict)

        Returns:
            Complete prompt string for study guide generation
        """
        logger.info("Building study guide prompt...")

        # Initialize study guide builder
        study_builder = StudyGuidePromptBuilder(
            keywords_report=self.keywords,
            difficulty=self.difficulty,
            grade=self.grade,
            page_count=5  # Default 5 pages
        )

        # Generate base study guide prompt
        base_prompt = study_builder.generate_curriculum_narrative_prompt()

        # Add purpose-driven focus if specified
        if self.purpose:
            purpose_focus = self.difficulty_engine.generate_purpose_prompt(
                purpose=self.purpose,
                topic=self.topic
            )
            base_prompt += f"\n\n{purpose_focus}"

        # Add format constraints (Markdown/PDF)
        primary_format = self.format_adapter.formats[0] if self.format_adapter.formats else 'markdown'
        enhanced_prompt = self.format_adapter.inject_format_rules(base_prompt, primary_format)

        logger.info(f"Study guide prompt built: {len(enhanced_prompt)} chars")
        return enhanced_prompt

    def build_handout_prompt(self, content_request) -> str:
        """
        Build complete handout/visual prompt.

        Args:
            content_request: ContentRequest object (or dict)

        Returns:
            Complete prompt string for handout generation
        """
        logger.info("Building handout prompt...")

        # Initialize handout builder
        handout_builder = HandoutPromptBuilder(
            topic=self.topic,
            grade=self.grade,
            keywords=self.keywords
        )

        # Build multi-part handout prompt
        prompt_parts = [
            f"Create visual representations for a {self.grade} handout on {self.topic}.",
            "",
            "## TASK 1: Mathematical Formulas",
            handout_builder.generate_latex_equation_prompt(),
            "",
            "## TASK 2: Timelines or Flowcharts",
            handout_builder.generate_mermaid_timeline_prompt(),
            "",
            "## TASK 3: Diagram Descriptions",
            handout_builder.generate_diagram_description_prompt()
        ]

        base_prompt = "\n".join(prompt_parts)

        # Add format constraints (HTML for rendering Mermaid/MathJax)
        enhanced_prompt = self.format_adapter.inject_format_rules(base_prompt, 'html')

        logger.info(f"Handout prompt built: {len(enhanced_prompt)} chars")
        return enhanced_prompt

    def build_all_prompts(self) -> Dict[str, str]:
        """
        Build all configured prompts based on output_config.

        Returns:
            Dictionary with keys: 'quiz', 'study_guide', 'handout' (if enabled)
        """
        prompts = {}

        if self.output_config.get('quiz', False):
            prompts['quiz'] = self.build_quiz_prompt(self.context)

        if self.output_config.get('studyGuide', False):
            prompts['study_guide'] = self.build_study_guide_prompt(self.context)

        if self.output_config.get('handout', False):
            prompts['handout'] = self.build_handout_prompt(self.context)

        logger.info(f"Built {len(prompts)} prompts: {list(prompts.keys())}")
        return prompts

    def validate_prompt(self, prompt: str, output_type: str) -> tuple:
        """
        Validate a generated prompt for quality and alignment.

        Args:
            prompt: The generated prompt
            output_type: Type of output ('quiz', 'study_guide', 'handout')

        Returns:
            Tuple of (is_valid: bool, issues: List[str])
        """
        issues = []

        # Validate difficulty alignment
        is_difficulty_valid, difficulty_issues = self.difficulty_engine.validate_difficulty_alignment(
            prompt=prompt,
            difficulty=self.difficulty
        )

        if not is_difficulty_valid:
            issues.extend(difficulty_issues)

        # Validate format constraints (if applicable)
        if output_type == 'quiz':
            is_format_valid, format_issues = self.format_adapter.validate_output_format(
                output=prompt,
                format_type='csv'
            )
            if not is_format_valid:
                issues.extend(format_issues)

        # Check for hallucination safeguards
        if 'do not generate' not in prompt.lower() and 'not found in sources' not in prompt.lower():
            issues.append("Prompt should include hallucination safeguards (e.g., 'Do not generate facts not found in sources')")

        is_valid = len(issues) == 0
        return is_valid, issues


# Convenience function for simple prompt generation
def generate_prompts_from_context(context: Dict) -> Dict[str, str]:
    """
    Convenience function to generate all prompts from a context dictionary.

    Args:
        context: ContentRequest context dictionary

    Returns:
        Dictionary of generated prompts
    """
    orchestrator = PromptOrchestrator(context)
    return orchestrator.build_all_prompts()


__all__ = [
    'PromptOrchestrator',
    'InputSourcePromptBuilder',
    'QuizPromptBuilder',
    'StudyGuidePromptBuilder',
    'HandoutPromptBuilder',
    'DifficultyEngine',
    'OutputFormatAdapter',
    'generate_prompts_from_context'
]
