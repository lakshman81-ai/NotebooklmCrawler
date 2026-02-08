"""
Module A: Input Source Prompt Generator

Purpose: Generate optimized search/discovery prompts based on educational parameters.
This module implements the "Strategic Data Ingestion" best practices from the NotebookLM report.

Based on Section 2.1: "Optimizing Search Logic for Grade 8 Gravity"
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class InputSourcePromptBuilder:
    """
    Generates optimized search queries targeting high-quality educational sources.

    Maps (grade, subject, topic, difficulty, keywords) → search prompts that target:
    - Tier 1: Canonical sources (CK-12, Khan Academy, OpenStax)
    - Tier 2: Engagement sources (Byjus, Education.com, NASA Space Place)
    - Tier 3: Extension sources (College-level texts for advanced students)
    """

    # Trusted educational source domains
    CANONICAL_SOURCES = ["CK-12", "Khan Academy", "OpenStax"]
    ENGAGEMENT_SOURCES = ["Byjus", "Education.com", "NASA Space Place", "National Geographic"]
    EXTENSION_SOURCES = ["OpenStax College Physics", "MIT OpenCourseWare"]

    # Subject-specific source mappings
    SUBJECT_SOURCES = {
        "Physics": ["CK-12 physical science", "Khan Academy physics", "Byjus physics"],
        "Chemistry": ["CK-12 chemistry", "Khan Academy chemistry", "Byjus chemistry"],
        "Biology": ["CK-12 life science", "Khan Academy biology", "Byjus biology"],
        "Math": ["CK-12 math", "Khan Academy math", "Byjus math"],
        "General": ["CK-12", "Khan Academy", "Byjus"]
    }

    def __init__(self, grade: str, subject: str, topic: str,
                 difficulty: str, keywords: List[str]):
        """
        Initialize the prompt builder with educational parameters.

        Args:
            grade: Target grade level (e.g., "Grade 8", "High School")
            subject: Subject area (e.g., "Physics", "Chemistry", "Math")
            topic: Main topic (e.g., "Gravity", "Chemical Reactions")
            difficulty: Difficulty level ("Easy", "Medium", "Hard")
            keywords: List of subtopics/keywords (e.g., ["mass vs weight", "microgravity"])
        """
        self.grade = grade
        self.subject = subject
        self.topic = topic
        self.difficulty = difficulty
        self.keywords = keywords if isinstance(keywords, list) else []

        # Extract reading level from grade
        self.reading_level = self._extract_reading_level(grade)

        logger.info(f"InputSourcePromptBuilder initialized: {grade} {subject} - {topic}")

    def _extract_reading_level(self, grade: str) -> str:
        """
        Extract reading level descriptor from grade string.

        Examples:
            "Grade 8" → "middle school"
            "Grade 12" or "High School" → "high school"
            "General" → "general education"
        """
        grade_lower = grade.lower()

        if "grade" in grade_lower:
            # Extract grade number
            import re
            match = re.search(r'\d+', grade)
            if match:
                grade_num = int(match.group())
                if grade_num <= 5:
                    return "elementary school"
                elif grade_num <= 8:
                    return "middle school"
                else:
                    return "high school"

        if "high school" in grade_lower:
            return "high school"

        return "general education"

    def generate_textbook_search(self) -> str:
        """
        Targets core textbooks (CK-12, OpenStax, Khan Academy).

        Returns:
            Search query string optimized for educational textbooks

        Example:
            "CK-12 physical science gravity grade 8 mass weight Newton open educational resources"
        """
        # Get subject-specific sources
        sources = self.SUBJECT_SOURCES.get(self.subject, self.SUBJECT_SOURCES["General"])

        # Build query components
        components = [
            sources[0],  # Primary source (e.g., "CK-12 physical science")
            self.topic.lower(),
            self.grade.lower(),
            " ".join(self.keywords).lower() if self.keywords else "",
            "open educational resources"
        ]

        # Filter out empty components and join
        query = " ".join([c for c in components if c])

        logger.debug(f"Textbook search query: {query}")
        return query

    def generate_conceptual_search(self) -> str:
        """
        Targets analogies and conceptual explanations.

        Returns:
            Search query focused on conceptual understanding

        Example:
            "Grade 8 physics gravity conceptual explanation mass vs weight distinction"
        """
        components = [
            self.grade,
            self.subject.lower(),
            self.topic.lower(),
            "conceptual explanation",
            " ".join(self.keywords).lower() if self.keywords else "",
            "distinction" if len(self.keywords) > 1 else "analogy"
        ]

        query = " ".join([c for c in components if c])

        logger.debug(f"Conceptual search query: {query}")
        return query

    def generate_application_search(self) -> str:
        """
        Targets real-world examples and experiments.

        Returns:
            Search query for practical applications

        Example:
            "Byjus Khan academy education gravity resources microgravity experiments middle school text only"
        """
        # Get engagement sources
        sources = " ".join(self.ENGAGEMENT_SOURCES[:2])

        components = [
            sources,
            "education",
            self.topic.lower(),
            "resources" if not self.keywords else " ".join(self.keywords[:2]).lower(),
            "experiments" if self.subject in ["Physics", "Chemistry", "Biology"] else "examples",
            self.reading_level,
            "text only"  # Prioritize text over video for better parsing
        ]

        query = " ".join([c for c in components if c])

        logger.debug(f"Application search query: {query}")
        return query

    def generate_misconception_search(self) -> str:
        """
        Targets common student errors for quiz generation.

        Returns:
            Search query for misconceptions

        Example:
            "common student misconceptions gravity mass weight middle school"
        """
        components = [
            "common student misconceptions",
            self.topic.lower(),
            " ".join(self.keywords).lower() if self.keywords else "",
            self.reading_level
        ]

        query = " ".join([c for c in components if c])

        logger.debug(f"Misconception search query: {query}")
        return query

    def generate_multi_source_strategy(self) -> Dict[str, str]:
        """
        Returns dictionary of search types with weighted prompts.

        This implements the "Boolean-style specificity" from the report (Section 2.1.1).

        Returns:
            Dictionary with keys:
                - primary_search: Textbook-focused
                - conceptual_search: Analogy-focused
                - application_search: Real-world examples
                - misconception_search: Common errors
                - format_preferences: Preferred formats
                - source_weighting: Toggle recommendations
        """
        strategy = {
            "primary_search": self.generate_textbook_search(),
            "conceptual_search": self.generate_conceptual_search(),
            "application_search": self.generate_application_search(),
            "misconception_search": self.generate_misconception_search(),
            "format_preferences": ["HTML", "PDF with diagrams"],
            "source_weighting": self._generate_source_weighting()
        }

        logger.info(f"Multi-source strategy generated with {len(strategy)} components")
        return strategy

    def _generate_source_weighting(self) -> Dict[str, List[str]]:
        """
        Generate source weighting recommendations based on difficulty level.

        Returns:
            Dictionary with 'toggle_on' and 'toggle_off' lists
        """
        toggle_on = []
        toggle_off = []

        # Difficulty-based source selection
        if self.difficulty in ["Easy", "Medium"]:
            # Grade-level sources
            toggle_on = ["CK-12", "Khan Academy", "Byjus"]
            toggle_off = ["OpenStax College Physics", "MIT OpenCourseWare", "Research papers"]
        else:  # Hard
            # Include extension materials
            toggle_on = ["CK-12", "Khan Academy", "OpenStax", "Byjus"]
            toggle_off = ["Research papers"]  # Still avoid academic papers

        # Subject-specific adjustments
        if self.subject == "Physics":
            toggle_on.append("NASA Space Place")
        elif self.subject == "Biology":
            toggle_on.append("National Geographic")

        return {
            "toggle_on": toggle_on,
            "toggle_off": toggle_off
        }

    def generate_url_metadata_extraction_prompt(self, url: str) -> str:
        """
        Generate metadata extraction prompt for a specific URL.

        This is used when user provides a URL instead of search keywords.

        Args:
            url: The URL to analyze

        Returns:
            Prompt for extracting metadata from the URL content
        """
        domain = self._extract_domain(url)

        prompt = f"""Analyze this educational content from {domain} and extract metadata.

URL: {url}

OUTPUT FORMAT:
Provide a valid JSON object in a code block:
```json
{{
  "reading_level": "elementary/middle school/high school/college",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "standard_alignment": "NGSS/Common Core/etc",
  "content_type": "textbook/article/experiment/video transcript/other",
  "credibility_score": 1-5,
  "summary": "Brief 2-sentence summary of the content"
}}
```
"""

        return prompt

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for display purposes."""
        import re
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url
