"""
Multi-Report Orchestrator Module

Purpose: Generate multiple report versions (student, teacher, admin) from single content.
Applies persona transformations to prompts for different audiences.

Based on Phase 5 of the implementation plan.
"""

import logging
import copy
from typing import Dict, List
from contracts.content_request import ContentRequest
from ai_pipeline.output_prompt_injector import OutputPromptInjector
from prompt_modules import PromptOrchestrator

logger = logging.getLogger(__name__)


class MultiReportOrchestrator:
    """
    Orchestrates generation of multiple report versions for different audiences.

    Supports:
        - Student Version: Simplified language, guided examples, interactive elements
        - Teacher Version: Answer keys, learning objectives, NGSS/Common Core alignment
        - Admin Version: Standards mapping, assessment data, curriculum coverage
    """

    # Persona-specific prompt transformations
    PERSONA_PROMPTS = {
        'student': {
            'prefix': """Act as a Patient Tutor creating materials for students.

AUDIENCE: Students (not teachers)
TONE: Encouraging, accessible, engaging
LANGUAGE: Simplified but rigorous
APPROACH: Guide discovery, don't just give answers

""",
            'style_rules': [
                'Use "you" language (second person)',
                'Include practice problems with hints',
                'Add visual analogies and real-world examples',
                'Break complex concepts into step-by-step explanations',
                'Use encouraging language ("Try this...", "Notice how...")'
            ]
        },

        'teacher': {
            'prefix': """Act as a Colleague creating materials for fellow educators.

AUDIENCE: Teachers and instructors
TONE: Professional, collaborative
LANGUAGE: Educational terminology appropriate
APPROACH: Focus on pedagogy and learning objectives

""",
            'style_rules': [
                'Include learning objectives (SMART format)',
                'Map to educational standards (NGSS, Common Core)',
                'Provide answer keys with detailed explanations',
                'Suggest differentiation strategies',
                'Include formative assessment opportunities',
                'Add teaching tips and common misconceptions to address'
            ],
            'additional_sections': [
                '## Learning Objectives',
                '## Standards Alignment',
                '## Answer Key',
                '## Teaching Notes',
                '## Differentiation Strategies'
            ]
        },

        'admin': {
            'prefix': """Act as a Curriculum Auditor creating materials for administrators.

AUDIENCE: School administrators and curriculum coordinators
TONE: Formal, data-driven, standards-focused
LANGUAGE: Educational policy and assessment terminology
APPROACH: Emphasize alignment, coverage, and measurable outcomes

""",
            'style_rules': [
                'Map to specific standards (include standard codes)',
                'Include Bloom\'s Taxonomy level for each question',
                'Provide assessment rubrics with point values',
                'Calculate curriculum coverage percentages',
                'Highlight 21st century skills addressed',
                'Include vocabulary complexity metrics'
            ],
            'additional_sections': [
                '## Standards Coverage Matrix',
                '## Bloom\'s Taxonomy Distribution',
                '## Assessment Rubric',
                '## Vocabulary Analysis',
                '## Skills Framework Alignment (4Cs: Critical Thinking, Communication, Collaboration, Creativity)'
            ]
        }
    }

    def __init__(self, output_injector: OutputPromptInjector,
                 prompt_orchestrator: PromptOrchestrator):
        """
        Initialize multi-report orchestrator.

        Args:
            output_injector: OutputPromptInjector instance for DOM automation
            prompt_orchestrator: PromptOrchestrator instance for prompt generation
        """
        self.output_injector = output_injector
        self.prompt_orchestrator = prompt_orchestrator

        logger.info("MultiReportOrchestrator initialized")

    async def generate_all_reports(self, content_request: ContentRequest) -> Dict[str, Dict]:
        """
        Generate all requested report versions.

        Args:
            content_request: ContentRequest with multi_report_types specified

        Returns:
            Dictionary mapping report type to artifacts:
            {
                'student': {'quiz_csv': '...', 'study_guide_md': '...'},
                'teacher': {'quiz_csv': '...', 'study_guide_md': '...', 'answer_key_md': '...'},
                'admin': {'standards_map_md': '...', 'assessment_rubric_md': '...'}
            }
        """
        logger.info(f"Generating reports for types: {content_request.multi_report_types}")

        all_reports = {}

        for report_type in content_request.multi_report_types:
            if report_type not in self.PERSONA_PROMPTS:
                logger.warning(f"Unknown report type: {report_type}, skipping...")
                continue

            logger.info(f"=== Generating {report_type.upper()} version ===")

            # Apply persona transformation
            transformed_request = self._apply_persona_transformation(
                content_request, report_type
            )

            # Generate artifacts for this persona
            artifacts = await self.output_injector.inject_multi_stage_prompts(
                transformed_request
            )

            all_reports[report_type] = artifacts

            logger.info(f"✓ {report_type} version complete: {list(artifacts.keys())}")

        logger.info(f"Multi-report generation complete: {len(all_reports)} versions created")
        return all_reports

    def _apply_persona_transformation(self, request: ContentRequest,
                                     persona: str) -> ContentRequest:
        """
        Apply persona-specific transformations to content request.

        Args:
            request: Original ContentRequest
            persona: Target persona ('student', 'teacher', 'admin')

        Returns:
            Modified ContentRequest with persona-specific prompt adjustments
        """
        logger.debug(f"Applying {persona} persona transformation...")

        # Clone request to avoid modifying original
        transformed = copy.deepcopy(request)

        # Get persona configuration
        persona_config = self.PERSONA_PROMPTS[persona]

        # Modify custom_prompt with persona prefix
        persona_prefix = persona_config['prefix']
        style_rules = '\n'.join([f"- {rule}" for rule in persona_config['style_rules']])

        # If there's already a custom prompt, append to it
        if transformed.custom_prompt:
            transformed.custom_prompt = f"{persona_prefix}\n{style_rules}\n\n{transformed.custom_prompt}"
        else:
            # Build default custom prompt
            transformed.custom_prompt = f"{persona_prefix}\n{style_rules}"

        # Add additional sections for teacher/admin
        if 'additional_sections' in persona_config:
            additional_sections = '\n'.join(persona_config['additional_sections'])
            transformed.custom_prompt += f"\n\nREQUIRED ADDITIONAL SECTIONS:\n{additional_sections}"

        # Adjust output config based on persona
        if persona == 'teacher':
            # Teachers get answer keys
            transformed.output_config = transformed.output_config.copy()
            transformed.output_config['answerKey'] = True

        elif persona == 'admin':
            # Admins get standards mapping instead of student materials
            transformed.output_config = transformed.output_config.copy()
            transformed.output_config['standardsMapping'] = True
            transformed.output_config['assessmentRubric'] = True

        logger.debug(f"Persona transformation complete for {persona}")
        return transformed

    def _enhance_quiz_for_teacher(self, quiz_prompt: str) -> str:
        """
        Enhance quiz prompt with teacher-specific elements.

        Args:
            quiz_prompt: Base quiz prompt

        Returns:
            Enhanced prompt with answer explanations and rubrics
        """
        enhancement = """

TEACHER VERSION REQUIREMENTS:
- Add "Explanation" column after Correct_Answer_Text
- For each question, provide a 2-3 sentence explanation of why the correct answer is right
- Include "Common_Misconception" column noting typical student errors
- Add "Bloom_Level" column indicating cognitive level (Remember, Understand, Apply, Analyze, Evaluate, Create)
- Add "Standard_Code" column mapping to relevant educational standard (e.g., MS-PS2-2 for middle school physical science)
"""

        return quiz_prompt + enhancement

    def _enhance_study_guide_for_teacher(self, guide_prompt: str) -> str:
        """
        Enhance study guide prompt with teacher-specific sections.

        Args:
            guide_prompt: Base study guide prompt

        Returns:
            Enhanced prompt with lesson plan elements
        """
        enhancement = """

TEACHER VERSION REQUIREMENTS:
Include these additional sections:

## Learning Objectives (SMART Format)
- Students will be able to [verb] [content] [criteria]
- Example: "Students will be able to calculate gravitational force between two objects with 90% accuracy"

## Standards Alignment
- List relevant NGSS/Common Core standards with codes
- Example: "MS-PS2-2: Plan an investigation to provide evidence that the change in motion depends on forces"

## Answer Key
- Provide answers to all practice problems
- Include step-by-step solutions for complex problems

## Teaching Notes
- Suggested activities and demonstrations
- Common student misconceptions to address
- Differentiation strategies for diverse learners
- Estimated time for each section

## Formative Assessment Opportunities
- Checkpoints for understanding
- Questions to ask during instruction
- Exit ticket suggestions
"""

        return guide_prompt + enhancement

    def _create_standards_mapping_prompt(self, content_request: ContentRequest) -> str:
        """
        Create admin-specific standards mapping prompt.

        Args:
            content_request: ContentRequest with topic/grade info

        Returns:
            Prompt for generating standards coverage report
        """
        prompt = f"""Act as a Curriculum Auditor analyzing standards coverage.

TASK: Create a comprehensive Standards Coverage Matrix for {content_request.grade} {content_request.topic}.

Based on the provided sources, create a detailed mapping document.

## Output Structure:

### 1. Standards Identification
List all relevant educational standards covered:
- NGSS (Next Generation Science Standards) with codes
- Common Core State Standards (if applicable)
- State-specific standards (if identified in sources)

### 2. Coverage Matrix (Markdown Table)
Create a table with columns:
| Standard Code | Standard Description | Depth of Coverage | Evidence in Sources | Bloom's Level |

Depth of Coverage: Introduced | Developed | Mastered
Bloom's Level: Remember | Understand | Apply | Analyze | Evaluate | Create

### 3. Gap Analysis
- Standards mentioned but not fully covered
- Recommended supplemental materials
- Prerequisite knowledge required

### 4. Assessment Alignment
- How quiz questions map to standards
- Distribution of questions across standards
- Balance of cognitive complexity

### 5. 21st Century Skills Framework
Map content to 4Cs:
- Critical Thinking examples
- Communication opportunities
- Collaboration activities (suggested)
- Creativity applications

FORMAT: Markdown with clear section headers and tables
"""

        return prompt

    def generate_student_version_only(self, base_prompt: str) -> str:
        """
        Convenience method to quickly generate student version of any prompt.

        Args:
            base_prompt: Original prompt

        Returns:
            Student-friendly version
        """
        student_config = self.PERSONA_PROMPTS['student']
        prefix = student_config['prefix']
        style_rules = '\n'.join([f"- {rule}" for rule in student_config['style_rules']])

        return f"{prefix}\n{style_rules}\n\n{base_prompt}"


# Convenience function
async def generate_multi_version_reports(output_injector: OutputPromptInjector,
                                        content_request: ContentRequest) -> Dict[str, Dict]:
    """
    Convenience function for generating multi-version reports.

    Args:
        output_injector: OutputPromptInjector instance
        content_request: ContentRequest with multi_report_types specified

    Returns:
        Dictionary of all generated report versions
    """
    from prompt_modules import PromptOrchestrator

    orchestrator_prompt = PromptOrchestrator(content_request.model_dump())
    multi_orchestrator = MultiReportOrchestrator(output_injector, orchestrator_prompt)

    return await multi_orchestrator.generate_all_reports(content_request)
