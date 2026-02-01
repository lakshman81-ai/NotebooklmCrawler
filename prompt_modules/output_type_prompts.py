"""
Module B: Output Type Prompt Generator

Purpose: Generate format-specific prompts for study guides, quizzes, and handouts
based on educational requirements.

Based on Section 3: "Advanced Prompt Architectures for 'Create Your Own' Artifacts"
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class QuizPromptBuilder:
    """
    Generates prompts for quiz creation with strict formatting constraints.

    Implements "Format-Constraint Prompting" from Section 3.1 of the report.
    """

    def __init__(self, quiz_config: dict, difficulty: str,
                 grade: str, keywords_report: List[str]):
        """
        Initialize quiz prompt builder.

        Args:
            quiz_config: Dict with keys: mcq, ar, detailed, custom
            difficulty: Difficulty level (Easy/Medium/Hard)
            grade: Target grade level
            keywords_report: Focus keywords for content distribution
        """
        self.mcq_count = quiz_config.get('mcq', 10)
        self.ar_count = quiz_config.get('ar', 0)  # Assertion-Reasoning
        self.detailed_count = quiz_config.get('detailed', 0)
        self.custom_instructions = quiz_config.get('custom', '')
        self.difficulty = difficulty
        self.grade = grade
        self.keywords = keywords_report

        logger.info(f"QuizPromptBuilder: {self.mcq_count} MCQ, {self.ar_count} AR, {self.detailed_count} Detailed")

    def generate_strict_csv_prompt(self) -> str:
        """
        Generates "Strict CSV" prompt with exact formatting requirements.

        Returns strict CSV format prompt that prevents LLM from adding
        conversational filler (Section 3.1.2 of report).

        Returns:
            Formatted prompt string
        """
        total_questions = self.mcq_count + self.ar_count + self.detailed_count

        # Build content requirements based on keywords
        content_requirements = self._generate_content_distribution()

        # Difficulty descriptor
        difficulty_map = {
            "Easy": "Easy (Grade-level Standard)",
            "Medium": "Medium (Grade-level Standard)",
            "Hard": "Hard (Advanced Application)"
        }
        difficulty_desc = difficulty_map.get(self.difficulty, "Medium (Grade-level Standard)")

        prompt = f"""Act as a {self.grade} assessment specialist. Based exclusively on the active sources, generate a {total_questions}-question quiz.

DIFFICULTY LEVEL: {difficulty_desc}

FORMATTING RULES:
Output ONLY a raw code block containing CSV data.
Do not include any introductory text or closing remarks.
The Separator must be a comma ,
The Column Headers must be exactly: ID,Topic,Question_Text,Option_A,Option_B,Option_C,Option_D,Correct_Answer_Text

CONTENT REQUIREMENTS:
{content_requirements}

CRITICAL CONSTRAINTS:
- The 'Correct_Answer_Text' column must contain the full text of the correct answer, NOT just the letter (A/B/C/D). This is the last column.
- Do not generate any facts not explicitly found in the provided sources.
- Each question must have exactly 4 options (A, B, C, D).
- Avoid ambiguous wording - questions must have one clearly correct answer.

EXAMPLE ROW FORMAT:
1,Definitions,What creates gravity?,A planet's color,A planet's mass,A planet's speed,The atmosphere,A planet's mass

{self._add_custom_instructions()}

Begin CSV output now:"""

        logger.debug(f"Generated strict CSV prompt ({len(prompt)} chars)")
        return prompt

    def _generate_content_distribution(self) -> str:
        """
        Distribute questions across keywords/topics.

        Returns:
            Multi-line string with Q ranges mapped to topics
        """
        if not self.keywords or len(self.keywords) == 0:
            return "Questions should cover all key concepts from the sources."

        total_q = self.mcq_count
        keywords = self.keywords if isinstance(self.keywords, list) else [self.keywords]

        # Distribute questions across keywords
        q_per_keyword = max(1, total_q // len(keywords))
        distributions = []

        q_start = 1
        for i, keyword in enumerate(keywords[:3]):  # Limit to 3 main topics
            q_end = min(q_start + q_per_keyword - 1, total_q)
            distributions.append(f"Q{q_start}-Q{q_end}: Focus on {keyword}")
            q_start = q_end + 1

        # Remaining questions
        if q_start <= total_q:
            distributions.append(f"Q{q_start}-Q{total_q}: Synthesis and application across all topics")

        return "\n".join(distributions)

    def _add_custom_instructions(self) -> str:
        """Add custom instructions if provided."""
        if self.custom_instructions:
            return f"\nADDITIONAL INSTRUCTIONS:\n{self.custom_instructions}\n"
        return ""

    def generate_assertion_reasoning_prompt(self) -> str:
        """
        Generate prompt for Assertion-Reasoning (AR) questions.

        AR Format:
            Statement A: [Assertion]
            Statement B: [Reason]
            Options:
                A) Both A and B are correct, and B is the correct reason for A
                B) Both A and B are correct, but B is not the correct reason for A
                C) A is correct, but B is incorrect
                D) A is incorrect, but B is correct
        """
        if self.ar_count == 0:
            return ""

        prompt = f"""Generate {self.ar_count} Assertion-Reasoning questions based on the sources.

FORMAT for each question:
Statement A (Assertion): [Statement about a concept]
Statement B (Reason): [Statement that may or may not explain A]

Options (ALWAYS use these exact options):
A) Both A and B are correct, and B is the correct reason for A
B) Both A and B are correct, but B is not the correct reason for A
C) A is correct, but B is incorrect
D) A is incorrect, but B is correct

FOCUS: Test causal relationships and conceptual connections.

Target {self.ar_count} AR questions on: {', '.join(self.keywords) if self.keywords else 'key concepts from sources'}"""

        return prompt


class StudyGuidePromptBuilder:
    """
    Generates prompts for comprehensive study guides.

    Implements "Curriculum Narrative" approach from Section 3.2 of report.
    """

    def __init__(self, keywords_report: List[str], difficulty: str,
                 grade: str, page_count: int = 5):
        """
        Initialize study guide prompt builder.

        Args:
            keywords_report: Focus areas for the guide
            difficulty: Difficulty level
            grade: Target grade
            page_count: Target page count (approx. 400-500 words per page)
        """
        self.keywords = keywords_report if isinstance(keywords_report, list) else []
        self.difficulty = difficulty
        self.grade = grade
        self.page_count = page_count
        self.target_word_count = page_count * 400  # ~400 words per page

        logger.info(f"StudyGuidePromptBuilder: {page_count} pages, {self.target_word_count} words target")

    def generate_curriculum_narrative_prompt(self) -> str:
        """
        Creates 'Curriculum Narrative' prompt with structured sections.

        Returns:
            Prompt for comprehensive study guide generation
        """
        # Word count distribution
        intro_words = 400
        core_words = 500
        history_words = 400
        application_words = 400
        glossary_items = min(10, len(self.keywords) * 2) if self.keywords else 10

        # Build structure
        prompt = f"""Generate a comprehensive '{self.grade} Study Guide' based on the sources. The output must be extensive, detailed, and formatted as a formal educational handout.

TARGET LENGTH: Approximately {self.target_word_count} words ({self.page_count} pages)

STRUCTURE:

# Introduction: The Core Concept (approx. {intro_words} words)
Define the main concept using precise terminology from the sources.
Include a blockquote analogy to make the concept relatable.

# Key Concepts Explained (approx. {core_words} words)
{self._generate_key_concepts_section()}
Create text-based comparison tables where appropriate.
Explain distinctions clearly with examples from sources.

# Historical Context & Development (approx. {history_words} words)
Narrate the evolution of understanding on this topic.
Include key scientists, experiments, and theoretical shifts.
Use analogies found in source texts.

# Real-World Applications (approx. {application_words} words)
Explain practical applications and observable phenomena.
Connect theory to everyday experiences.
Include examples from sources (experiments, technologies, natural phenomena).

# Glossary of Terms
Define at least {glossary_items} key terms precisely as found in sources.
Format: **Term**: Definition

STYLE REQUIREMENTS:
- Educational tone, accessible to {self._get_reading_age()}-year-olds but rigorous
- Continuous prose with clear transitions between sections
- Use Markdown headers (# ## ###) for structure
- Include citations: [Source: Title] after borrowed concepts

CRITICAL CONSTRAINTS:
- Do not generate facts not found in provided sources
- If a concept is not mentioned in sources, exclude it from output
- Prefer definitions and explanations directly quoted or paraphrased from sources
- Avoid speculation beyond source material

{self._add_difficulty_focus()}"""

        logger.debug(f"Generated curriculum narrative prompt ({len(prompt)} chars)")
        return prompt

    def _generate_key_concepts_section(self) -> str:
        """Generate the key concepts section structure based on keywords."""
        if not self.keywords or len(self.keywords) == 0:
            return "Identify and explain the 3-5 most important concepts from the sources."

        concepts = []
        for i, keyword in enumerate(self.keywords[:5], 1):
            concepts.append(f"{i}. {keyword.title()}")

        return "Focus on these concepts:\n" + "\n".join(concepts) + "\n"

    def _get_reading_age(self) -> int:
        """Extract approximate reading age from grade."""
        import re
        match = re.search(r'\d+', self.grade)
        if match:
            grade_num = int(match.group())
            return grade_num + 5  # Grade 8 → age 13
        return 14  # Default

    def _add_difficulty_focus(self) -> str:
        """Add difficulty-specific guidance."""
        if self.difficulty == "Easy":
            return "\nFOCUS: Clear definitions, basic examples, step-by-step explanations."
        elif self.difficulty == "Hard":
            return "\nFOCUS: In-depth analysis, complex applications, connections across concepts."
        return "\nFOCUS: Balance definitions with applications, include cause-effect relationships."

    def generate_comparison_table_prompt(self, concept_a: str, concept_b: str) -> str:
        """
        Generate prompt for comparison tables (e.g., Mass vs Weight).

        Args:
            concept_a: First concept
            concept_b: Second concept

        Returns:
            Prompt for Markdown table generation
        """
        prompt = f"""Create a comparison table contrasting {concept_a} and {concept_b}.

FORMAT: Markdown table

REQUIRED ROWS:
| Property | {concept_a} | {concept_b} |
|----------|-------------|-------------|
| Definition | ... | ... |
| Does it change? | ... | ... |
| Unit of Measurement | ... | ... |
| Example | ... | ... |

SOURCE REQUIREMENT: Use exact definitions from source material.
Include source citation below table: [Source: Title]"""

        return prompt


class HandoutPromptBuilder:
    """
    Generates prompts for visual handouts with equations, flowcharts, timelines.

    Implements LaTeX and Mermaid.js code generation from Section 3.3 of report.
    """

    def __init__(self, topic: str, grade: str, keywords: List[str]):
        """
        Initialize handout prompt builder.

        Args:
            topic: Main topic for visuals
            grade: Target grade
            keywords: Focus areas for visual representation
        """
        self.topic = topic
        self.grade = grade
        self.keywords = keywords if isinstance(keywords, list) else []

        logger.info(f"HandoutPromptBuilder: {topic} for {grade}")

    def generate_latex_equation_prompt(self) -> str:
        """
        Requests LaTeX-formatted equations with variable legends.

        Returns:
            Prompt for LaTeX equation generation
        """
        prompt = f"""Provide the key mathematical formula related to {self.topic} from the sources.

FORMAT REQUIREMENTS:
1. Output the equation in LaTeX syntax wrapped in double dollar signs: $$equation$$
2. Below the equation, provide a bulleted legend explaining each variable in simple {self.grade} terms

EXAMPLE FORMAT:
$$F = ma$$

Where:
- $F$ = Force (measured in Newtons)
- $m$ = Mass (measured in kilograms)
- $a$ = Acceleration (measured in meters per second squared)

CRITICAL: Only include formulas explicitly mentioned in the sources.
If no formula exists, state: "No mathematical formula provided in sources."
"""

        return prompt

    def generate_mermaid_flowchart_prompt(self, process_description: str = "") -> str:
        """
        Generates Mermaid.js flowchart prompts.

        Args:
            process_description: Description of process to visualize

        Returns:
            Prompt for Mermaid.js code generation
        """
        focus = process_description if process_description else f"a key process or concept related to {self.topic}"

        prompt = f"""Create a flowchart explaining {focus} using Mermaid.js syntax.

OUTPUT: Provide ONLY the Mermaid.js code block, no additional text.

FORMAT:
```mermaid
graph TD
    A[Start/Concept] --> B[Step 1]
    B --> C[Step 2]
    C --> D[Result/Conclusion]
```

REQUIREMENTS:
- Use simple, grade-appropriate language in nodes
- Maximum 6-8 nodes (keep it digestible for {self.grade})
- Use directional flow (TD for top-down or LR for left-right)
- Base the flow on explanations found in sources

If the concept is better represented as a timeline, use this format instead:
```mermaid
timeline
    title Evolution of Understanding
    Period 1 : Event : Description
    Period 2 : Event : Description
```
"""

        return prompt

    def generate_mermaid_timeline_prompt(self, events: List[str] = None) -> str:
        """
        Generate prompt for historical timeline.

        Args:
            events: Optional list of events to include

        Returns:
            Prompt for Mermaid.js timeline
        """
        events_guidance = ""
        if events:
            events_guidance = f"\nINCLUDE THESE EVENTS:\n" + "\n".join(f"- {e}" for e in events)

        prompt = f"""Create a chronological timeline of {self.topic} development based on the sources.

OUTPUT FORMAT: Mermaid.js timeline syntax

EXAMPLE:
```mermaid
timeline
    title History of {self.topic}
    1600s : Scientist Name : Discovery/Theory
    1800s : Scientist Name : Major Advancement
    1900s : Scientist Name : Modern Understanding
```

{events_guidance}

REQUIREMENTS:
- Only include historical information explicitly mentioned in sources
- Use approximate time periods if exact dates not provided
- Maximum 5-7 timeline entries
- Keep descriptions concise (under 10 words per entry)
"""

        return prompt

    def generate_diagram_description_prompt(self) -> str:
        """
        Generate text descriptions of visual layouts for later rendering.

        Returns:
            Prompt for diagram layout descriptions
        """
        prompt = f"""Describe visual diagrams that would aid understanding of {self.topic}.

For each diagram, provide:
1. **Diagram Type**: (e.g., Labeled Diagram, Process Flow, Comparison Chart)
2. **Title**: Clear, descriptive title
3. **Elements**: List all visual elements and labels
4. **Placement**: Describe spatial relationships
5. **Caption**: 1-2 sentence caption explaining the diagram
6. **Accessibility**: Color-blind friendly color suggestions

FORMAT: Markdown with clear structure

EXAMPLE:
### Diagram 1: Forces in Action

**Type**: Labeled Diagram
**Elements**:
- Central object (box)
- Arrow pointing down labeled "Gravitational Force (Fg)"
- Arrow pointing up labeled "Normal Force (Fn)"

**Caption**: This diagram shows the balanced forces acting on a stationary object resting on a surface.

Provide 2-3 diagram descriptions based on key concepts in the sources.
"""

        return prompt
