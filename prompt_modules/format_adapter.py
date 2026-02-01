"""
Module C: Output Format Recognition & Prompt Adaptation

Purpose: Recognize expected output format and modify prompts accordingly.
Ensures LLM outputs match target format specifications (CSV, PDF, HTML, DOCX).

Based on Section 3.1: "Format-Constraint Prompting"
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class OutputFormatAdapter:
    """
    Adapts prompts based on target output format requirements.

    Supports: CSV, PDF, HTML, DOCX, Markdown (default)
    """

    # Format-specific constraints
    FORMAT_CONSTRAINTS = {
        'csv': {
            'header': 'CSV FORMAT REQUIREMENTS',
            'rules': [
                'Output ONLY a raw code block containing CSV data',
                'Do not include any introductory text or closing remarks',
                'Do not use conversational language like "Here is your CSV..."',
                'Separator must be comma ,',
                'Escape commas within cell content with quotes',
                'No blank lines between rows',
                'First row must be column headers'
            ],
            'example': '```csv\nID,Name,Value\n1,Item A,100\n2,Item B,200\n```'
        },

        'pdf': {
            'header': 'PDF LAYOUT REQUIREMENTS',
            'rules': [
                'Include page break markers: <!-- PAGE_BREAK -->',
                'Specify image placements: [IMAGE: description | position: center/left/right]',
                'Use clear section headings with Markdown # ## ###',
                'Include table of contents markers: <!-- TOC -->',
                'Maintain consistent formatting for print readability',
                'Avoid excessive line breaks (will waste printed pages)'
            ],
            'example': 'Use <!-- PAGE_BREAK --> to start new page'
        },

        'html': {
            'header': 'HTML FORMAT REQUIREMENTS',
            'rules': [
                'Wrap output in complete HTML5 document structure',
                'Include <!DOCTYPE html> declaration',
                'Add <head> section with CDN scripts for Mermaid.js and MathJax',
                'Use semantic HTML tags: <article>, <section>, <aside>, <figure>',
                'Include proper heading hierarchy (<h1>, <h2>, <h3>)',
                'Add CSS classes for styling hooks',
                'Ensure accessibility with alt text and ARIA labels'
            ],
            'cdn_scripts': [
                '<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs"; mermaid.initialize({ startOnLoad: true });</script>',
                '<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>',
                '<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'
            ]
        },

        'docx': {
            'header': 'DOCX (Word) FORMAT REQUIREMENTS',
            'rules': [
                'Use Markdown syntax compatible with Pandoc conversion',
                'Use ### for headings (will convert to Word heading styles)',
                'Use **bold** and *italic* for emphasis',
                'Tables should use Markdown pipe syntax',
                'For complex formatting, include Pandoc-specific syntax',
                'Avoid HTML tags (use Markdown equivalents)'
            ],
            'example': '**Bold text** and *italic text* for Word compatibility'
        },

        'sheets': {
            'header': 'GOOGLE SHEETS / EXCEL FORMAT REQUIREMENTS',
            'rules': [
                'Same as CSV format but include formula syntax where appropriate',
                'Use Excel formula syntax: =SUM(A1:A10) or =IF(B1>0,"Yes","No")',
                'Include data validation rules as comments: <!-- VALIDATION: A2:A100 must be numeric -->',
                'For dropdown lists, include options: <!-- DROPDOWN: Option1,Option2,Option3 -->',
                'Reserve first row for column headers with clear names'
            ],
            'example': '=IF(G2=D2,"Correct","Incorrect") for auto-grading'
        },

        'markdown': {
            'header': 'MARKDOWN FORMAT REQUIREMENTS',
            'rules': [
                'Use standard Markdown syntax',
                'Use # ## ### for heading hierarchy',
                'Use ``` for code blocks with language specification',
                'Use > for blockquotes',
                'Use - or * for unordered lists',
                'Use 1. 2. 3. for ordered lists',
                'Use | for tables with header separator'
            ],
            'example': '```python\ncode here\n```'
        }
    }

    def __init__(self, output_config: dict):
        """
        Initialize format adapter.

        Args:
            output_config: Dict with 'formats' key containing list of target formats
        """
        self.formats = output_config.get('formats', ['markdown'])

        # Normalize format names
        self.formats = [self._normalize_format(f) for f in self.formats]

        logger.info(f"OutputFormatAdapter initialized for formats: {self.formats}")

    def _normalize_format(self, format_type: str) -> str:
        """
        Normalize format string to lowercase standard values.

        Args:
            format_type: Input format (may be 'CSV', 'Pdf', etc.)

        Returns:
            Lowercase normalized format
        """
        format_lower = format_type.lower()

        # Map alternative names
        if format_lower in ['excel', 'xlsx', 'xls']:
            return 'sheets'
        elif format_lower in ['word', 'doc']:
            return 'docx'
        elif format_lower in ['htm']:
            return 'html'
        elif format_lower in ['md']:
            return 'markdown'

        return format_lower

    def get_format_constraints(self, format_type: str) -> dict:
        """
        Get format-specific constraints.

        Args:
            format_type: Target format (csv, pdf, html, docx, sheets, markdown)

        Returns:
            Dictionary with keys: header, rules, example (if available)
        """
        format_type = self._normalize_format(format_type)

        constraints = self.FORMAT_CONSTRAINTS.get(
            format_type,
            self.FORMAT_CONSTRAINTS['markdown']  # Default
        )

        logger.debug(f"Retrieved constraints for {format_type}: {len(constraints['rules'])} rules")
        return constraints

    def inject_format_rules(self, base_prompt: str, format_type: str) -> str:
        """
        Inject format-specific rules into a base prompt.

        Args:
            base_prompt: Original prompt text
            format_type: Target output format

        Returns:
            Enhanced prompt with format constraints appended
        """
        format_type = self._normalize_format(format_type)

        # Get constraints for this format
        constraints = self.get_format_constraints(format_type)

        # Build format rules section
        rules_text = f"\n\n{constraints['header']}:\n"
        rules_text += "\n".join(f"- {rule}" for rule in constraints['rules'])

        if 'example' in constraints:
            rules_text += f"\n\nEXAMPLE:\n{constraints['example']}"

        # Special handling for HTML (add CDN scripts info)
        if format_type == 'html' and 'cdn_scripts' in constraints:
            rules_text += "\n\nREQUIRED CDN SCRIPTS (include in <head>):\n"
            rules_text += "\n".join(constraints['cdn_scripts'])

        # Append to base prompt
        enhanced_prompt = base_prompt + rules_text

        logger.debug(f"Injected {format_type} format rules into prompt (+{len(rules_text)} chars)")
        return enhanced_prompt

    def inject_multi_format_rules(self, base_prompt: str) -> str:
        """
        Inject rules for all configured formats.

        If multiple formats are configured, adds guidance for each.

        Args:
            base_prompt: Original prompt text

        Returns:
            Enhanced prompt with all format constraints
        """
        if not self.formats or len(self.formats) == 0:
            return base_prompt

        # Primary format (first in list)
        primary_format = self.formats[0]

        # For single format, just inject that
        if len(self.formats) == 1:
            return self.inject_format_rules(base_prompt, primary_format)

        # For multiple formats, add note
        enhanced_prompt = base_prompt + f"\n\nPRIMARY OUTPUT FORMAT: {primary_format.upper()}"
        enhanced_prompt += f"\nNote: Output will be converted to additional formats: {', '.join(self.formats[1:])}"

        # Inject primary format rules
        enhanced_prompt = self.inject_format_rules(enhanced_prompt, primary_format)

        return enhanced_prompt

    def get_negative_constraints(self, format_type: str) -> List[str]:
        """
        Get "negative constraints" - things to avoid for this format.

        Args:
            format_type: Target format

        Returns:
            List of constraint strings
        """
        format_type = self._normalize_format(format_type)

        negative_constraints = {
            'csv': [
                'Do not add any explanatory text before or after the CSV',
                'Do not use pipe | or tab separators',
                'Do not add blank lines for readability',
                'Do not add row numbers as a separate column (unless specified in headers)'
            ],
            'pdf': [
                'Do not use excessive whitespace (wastes printed pages)',
                'Do not use colors that don\'t print well (prefer high contrast)',
                'Do not break tables across page boundaries without headers'
            ],
            'html': [
                'Do not use inline styles (use classes instead)',
                'Do not use deprecated HTML tags (<font>, <center>, etc.)',
                'Do not forget alt text for images'
            ],
            'docx': [
                'Do not use HTML tags (use Markdown)',
                'Do not use complex CSS (won\'t convert to Word)',
                'Do not use Unicode characters that may not render in Word'
            ],
            'markdown': [
                'Do not mix HTML and Markdown unnecessarily',
                'Do not use inconsistent heading levels (don\'t skip from # to ###)'
            ]
        }

        return negative_constraints.get(format_type, [])

    def add_negative_constraints(self, prompt: str, format_type: str) -> str:
        """
        Add negative constraints to prompt.

        Args:
            prompt: Base prompt
            format_type: Target format

        Returns:
            Prompt with negative constraints added
        """
        negatives = self.get_negative_constraints(format_type)

        if not negatives:
            return prompt

        negative_text = "\n\nCRITICAL - DO NOT:\n"
        negative_text += "\n".join(f"- {constraint}" for constraint in negatives)

        enhanced_prompt = prompt + negative_text

        logger.debug(f"Added {len(negatives)} negative constraints for {format_type}")
        return enhanced_prompt

    def validate_output_format(self, output: str, format_type: str) -> tuple:
        """
        Validate that output matches format requirements.

        Args:
            output: Generated output text
            format_type: Expected format

        Returns:
            Tuple of (is_valid: bool, issues: List[str])
        """
        format_type = self._normalize_format(format_type)
        issues = []

        # CSV validation
        if format_type == 'csv':
            if not output.strip().startswith(('```csv', 'ID,', 'Column')):
                issues.append("CSV output should start with headers or code block")

            if 'Here is' in output or 'Below is' in output:
                issues.append("CSV contains conversational text (should be pure data)")

        # HTML validation
        elif format_type == 'html':
            if '<!DOCTYPE html>' not in output:
                issues.append("HTML missing DOCTYPE declaration")

            if '<head>' not in output or '</head>' not in output:
                issues.append("HTML missing head section")

        # PDF validation
        elif format_type == 'pdf':
            # Check for page break markers if long content
            if len(output) > 5000 and '<!-- PAGE_BREAK -->' not in output:
                issues.append("Long PDF content missing page break markers")

        is_valid = len(issues) == 0
        return is_valid, issues
