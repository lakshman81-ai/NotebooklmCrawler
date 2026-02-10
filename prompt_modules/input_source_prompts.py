import os
import logging
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class InputSourcePromptBuilder:
    """
    Generates prompts using Jinja2 templates.
    """

    def __init__(self, grade: str, subject: str, topic: str,
                 difficulty: str, keywords: List[str]):

        self.context = {
            "grade": grade,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "keywords": keywords if isinstance(keywords, list) else [],
            "reading_level": self._extract_reading_level(grade)
        }

        # Load Templates
        # Assuming templates/ is at the project root or relative to this file
        # This file: prompt_modules/input_source_prompts.py
        # Root: ../
        # Templates: ../templates/

        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
        self.env = Environment(loader=FileSystemLoader(template_dir))

        logger.info(f"InputSourcePromptBuilder initialized (Jinja2) with templates at: {template_dir}")

    def _extract_reading_level(self, grade: str) -> str:
        grade_lower = grade.lower()
        if "grade" in grade_lower:
            import re
            match = re.search(r'\d+', grade)
            if match:
                grade_num = int(match.group())
                if grade_num <= 5: return "elementary school"
                elif grade_num <= 8: return "middle school"
                else: return "high school"
        if "high school" in grade_lower: return "high school"
        return "general education"

    def generate_search_query(self) -> str:
        template = self.env.get_template("search_query.j2")
        return template.render(**self.context).strip()

    def generate_notebooklm_prompt(self, output_config: Dict, custom_prompt: str = "") -> str:
        template = self.env.get_template("notebooklm_input.j2")

        # Merge extra context
        render_ctx = self.context.copy()
        render_ctx["outputs"] = output_config
        render_ctx["custom_prompt"] = custom_prompt
        # Pass quizConfig if nested in output_config or check context
        if "quizConfig" not in render_ctx:
             render_ctx["quizConfig"] = output_config.get("quizConfig", {})

        return template.render(**render_ctx).strip()

    def generate_url_metadata_extraction_prompt(self, url: str) -> str:
        return f"Analyze this educational content from {url} and extract metadata."
