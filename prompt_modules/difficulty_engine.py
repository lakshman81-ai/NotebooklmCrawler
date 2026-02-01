"""
Module D: Difficulty & Purpose-Aware Prompt Engineering

Purpose: Adjust prompt complexity based on difficulty level and learning objectives.
Maps difficulty to Bloom's Taxonomy cognitive levels.

Based on best practices for educational scaffolding and assessment design.
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class DifficultyEngine:
    """
    Maps difficulty levels to Bloom's Taxonomy and generates appropriate constraints.

    Difficulty Mapping:
        - Easy: Remember, Understand (Identify level)
        - Medium: Apply, Analyze (Connect level)
        - Hard: Evaluate, Create (Extend level)
    """

    # Bloom's Taxonomy Mapping
    TAXONOMY_MAP = {
        'Easy': {
            'levels': ['Remember', 'Understand'],
            'description': 'Identify level - Focus on definitions, basic facts, and identification of key terms'
        },
        'Medium': {
            'levels': ['Apply', 'Analyze'],
            'description': 'Connect level - Focus on relationships, cause-and-effect, and connecting concepts'
        },
        'Hard': {
            'levels': ['Evaluate', 'Create'],
            'description': 'Extend level - Focus on applications, scenario-based analysis, and synthesis'
        }
    }

    # Question Verbs by Difficulty
    QUESTION_VERBS = {
        'Easy': ['Define', 'List', 'Identify', 'State', 'Name', 'Label', 'Match', 'Recall'],
        'Medium': ['Compare', 'Explain', 'Calculate', 'Distinguish', 'Classify', 'Demonstrate', 'Interpret'],
        'Hard': ['Evaluate', 'Design', 'Justify', 'Predict', 'Synthesize', 'Critique', 'Formulate', 'Hypothesize']
    }

    # Verbs to Avoid by Difficulty
    AVOID_VERBS = {
        'Easy': ['Evaluate', 'Critique', 'Synthesize'],  # Too advanced
        'Medium': ['List', 'Recall', 'Name'],  # Too basic
        'Hard': ['Define', 'Label', 'State']  # Too simple
    }

    def __init__(self):
        logger.info("DifficultyEngine initialized with Bloom's Taxonomy mapping")

    def get_question_verbs(self, difficulty: str) -> List[str]:
        """
        Get appropriate question verbs for the difficulty level.

        Args:
            difficulty: 'Easy', 'Medium', or 'Hard'

        Returns:
            List of action verbs appropriate for the difficulty

        Examples:
            Easy: ['Define', 'List', 'Identify']
            Medium: ['Compare', 'Explain', 'Calculate']
            Hard: ['Evaluate', 'Design', 'Justify']
        """
        difficulty = self._normalize_difficulty(difficulty)
        verbs = self.QUESTION_VERBS.get(difficulty, self.QUESTION_VERBS['Medium'])

        logger.debug(f"Question verbs for {difficulty}: {verbs[:3]}...")
        return verbs

    def get_bloom_levels(self, difficulty: str) -> List[str]:
        """
        Get Bloom's Taxonomy levels for the difficulty.

        Args:
            difficulty: 'Easy', 'Medium', or 'Hard'

        Returns:
            List of Bloom's taxonomy levels
        """
        difficulty = self._normalize_difficulty(difficulty)
        levels = self.TAXONOMY_MAP[difficulty]['levels']

        logger.debug(f"Bloom's levels for {difficulty}: {levels}")
        return levels

    def generate_difficulty_constraints(self, difficulty: str, purpose: str = "") -> str:
        """
        Generate difficulty constraint block for prompts.

        Args:
            difficulty: Difficulty level
            purpose: Optional learning objective (e.g., "improve assertion reasoning")

        Returns:
            Multi-line constraint text for inclusion in prompts

        Example Output:
            ```
            DIFFICULTY LEVEL: Medium (Grade 8 Standard)
            COGNITIVE FOCUS: Apply and Analyze (Bloom's Taxonomy)
            PURPOSE: Distinguish between mass and weight in different gravitational contexts
            QUESTION VERBS: Use 'Compare', 'Explain', 'Calculate', 'Distinguish'
            AVOID: Memorization questions, Definition recall
            ```
        """
        difficulty = self._normalize_difficulty(difficulty)

        # Get taxonomy info
        taxonomy = self.TAXONOMY_MAP[difficulty]
        bloom_levels = taxonomy['levels']
        description = taxonomy['description']

        # Get verbs
        use_verbs = ', '.join(f"'{v}'" for v in self.QUESTION_VERBS[difficulty][:4])
        avoid_verbs = ', '.join(self.AVOID_VERBS[difficulty][:2])

        # Build constraint block
        constraints = [
            f"DIFFICULTY LEVEL: {difficulty}",
            f"COGNITIVE FOCUS: {' and '.join(bloom_levels)} (Bloom's Taxonomy)",
        ]

        if purpose:
            constraints.append(f"PURPOSE: {purpose}")

        constraints.extend([
            f"QUESTION VERBS: Use {use_verbs}",
            f"AVOID: {avoid_verbs} questions"
        ])

        result = "\n".join(constraints)
        logger.debug(f"Generated difficulty constraints for {difficulty}")
        return result

    def generate_purpose_prompt(self, purpose: str, topic: str) -> str:
        """
        Generate purpose-specific prompt guidance.

        Args:
            purpose: Learning objective description
            topic: Main topic

        Returns:
            Purpose-focused prompt addition

        Purpose Types Handled:
            - "improve assertion reasoning"
            - "clarify concept: X vs Y"
            - "reinforce application: [concept]"
        """
        purpose_lower = purpose.lower()

        # Assertion Reasoning focus
        if "assertion" in purpose_lower or "reasoning" in purpose_lower:
            return self._generate_ar_focus(topic)

        # Concept clarification focus
        if "clarify" in purpose_lower or " vs " in purpose_lower:
            return self._generate_clarification_focus(purpose, topic)

        # Application focus
        if "application" in purpose_lower or "reinforce" in purpose_lower:
            return self._generate_application_focus(topic)

        # General purpose
        return f"PURPOSE-DRIVEN FOCUS: {purpose}\nAlign all content with this learning objective."

    def _generate_ar_focus(self, topic: str) -> str:
        """Generate Assertion-Reasoning specific guidance."""
        return f"""PURPOSE: Improve Assertion-Reasoning Skills

EMPHASIS:
- Causal relationship identification in {topic}
- Distinguishing correlation vs causation
- Evaluating logical dependencies between statements
- Testing conceptual connections, not just factual recall

AR QUESTION DESIGN:
- Statement A should present a key principle
- Statement B should be related but require critical thinking to evaluate if it's a valid reason
- Include plausible distractors that test understanding of causality"""

    def _generate_clarification_focus(self, purpose: str, topic: str) -> str:
        """Generate concept clarification guidance."""
        # Try to extract concepts being compared
        import re
        match = re.search(r'(\w+(?:\s+\w+)?)\s+vs\.?\s+(\w+(?:\s+\w+)?)', purpose, re.I)

        if match:
            concept_a, concept_b = match.groups()
            return f"""PURPOSE: Clarify Distinction Between {concept_a.title()} and {concept_b.title()}

EMPHASIS:
- Side-by-side comparison of {concept_a} vs {concept_b}
- Common misconceptions about these concepts
- Real-world examples that differentiate them
- Situations where each concept applies

CONTENT STRUCTURE:
- Use comparison tables
- Provide contrasting examples
- Explicitly state what makes them different"""
        else:
            return f"""PURPOSE: Concept Clarification for {topic}

EMPHASIS:
- Clear, precise definitions
- Common misconceptions to address
- Multiple representations of the concept
- Concrete examples"""

    def _generate_application_focus(self, topic: str) -> str:
        """Generate application-focused guidance."""
        return f"""PURPOSE: Reinforce Application Skills

EMPHASIS:
- Real-world applications of {topic}
- Scenario-based questions
- Transfer of knowledge to new contexts
- Problem-solving using the concept

CONTENT STRUCTURE:
- Practical examples from everyday life
- Step-by-step application processes
- Multiple contexts where the concept applies"""

    def _normalize_difficulty(self, difficulty: str) -> str:
        """
        Normalize difficulty string to standard values.

        Args:
            difficulty: Input difficulty (may be 'Identify', 'Connect', 'Extend', etc.)

        Returns:
            'Easy', 'Medium', or 'Hard'
        """
        difficulty_lower = difficulty.lower()

        # Map alternative names
        if difficulty_lower in ['identify', 'easy', 'basic', 'fundamental']:
            return 'Easy'
        elif difficulty_lower in ['connect', 'medium', 'intermediate', 'moderate']:
            return 'Medium'
        elif difficulty_lower in ['extend', 'hard', 'advanced', 'challenging']:
            return 'Hard'

        # Default to Medium
        logger.warning(f"Unknown difficulty '{difficulty}', defaulting to Medium")
        return 'Medium'

    def validate_difficulty_alignment(self, prompt: str, difficulty: str) -> Tuple[bool, List[str]]:
        """
        Validate that a prompt aligns with the specified difficulty.

        Args:
            prompt: The generated prompt text
            difficulty: Target difficulty level

        Returns:
            Tuple of (is_valid, [list_of_issues])
        """
        issues = []
        difficulty = self._normalize_difficulty(difficulty)

        # Check for inappropriate verbs
        avoid_verbs = self.AVOID_VERBS[difficulty]
        for verb in avoid_verbs:
            if verb.lower() in prompt.lower():
                issues.append(f"Prompt uses '{verb}' which is inappropriate for {difficulty} difficulty")

        # Check for required verbs (at least one should be present)
        required_verbs = self.QUESTION_VERBS[difficulty]
        has_required_verb = any(verb.lower() in prompt.lower() for verb in required_verbs)

        if not has_required_verb:
            issues.append(f"Prompt should use at least one {difficulty}-appropriate verb: {', '.join(required_verbs[:3])}")

        # Check for difficulty level mention
        if difficulty.lower() not in prompt.lower():
            issues.append(f"Prompt should explicitly state difficulty level: {difficulty}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_difficulty_score(self, difficulty: str) -> int:
        """
        Get numerical score for difficulty (for sorting/comparison).

        Args:
            difficulty: Difficulty level

        Returns:
            Integer score (1=Easy, 2=Medium, 3=Hard)
        """
        difficulty = self._normalize_difficulty(difficulty)
        scores = {'Easy': 1, 'Medium': 2, 'Hard': 3}
        return scores[difficulty]
