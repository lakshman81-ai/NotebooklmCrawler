"""
Module 3B: Output Prompt Injector (BOTH GUIDED & UNGUIDED)

Purpose: DOM automation for NotebookLM report generation.
Handles "Notebook guide" → "Create Your Own" navigation and prompt injection.

This module is used in BOTH guided and unguided modes since output generation
is the same regardless of how sources were added.
"""

import re
import logging
from typing import Dict
from playwright.async_api import Page

from prompt_modules import PromptOrchestrator

logger = logging.getLogger(__name__)


class OutputPromptInjector:
    """
    Handles output generation prompting for BOTH guided and unguided modes.

    Workflow:
        1. Navigate to "Notebook guide" → "Create Your Own"
        2. Inject formatted prompts (quiz/study guide/handout)
        3. Extract generated content from DOM
        4. Return structured results
    """

    def __init__(self, page: Page, prompt_orchestrator: PromptOrchestrator):
        """
        Initialize the output prompt injector.

        Args:
            page: Playwright Page object for browser automation
            prompt_orchestrator: PromptOrchestrator instance for prompt generation
        """
        self.page = page
        self.prompt_builder = prompt_orchestrator

        logger.info("OutputPromptInjector initialized (works for both GUIDED and UNGUIDED modes)")

    async def inject_multi_stage_prompts(self, content_request) -> Dict[str, str]:
        """
        Sequentially inject output prompts and extract results.

        Args:
            content_request: ContentRequest object or dict

        Returns:
            Dictionary with keys: 'quiz_csv', 'study_guide_md', 'visuals_md' (if enabled)

        Workflow:
            1. Quiz prompt → extract CSV
            2. Study guide prompt → extract Markdown
            3. Handout visuals prompt → extract Mermaid/LaTeX
        """
        logger.info("Starting multi-stage prompt injection...")

        results = {}

        # Extract output config
        output_config = getattr(content_request, 'output_config', {}) \
                        if hasattr(content_request, 'output_config') \
                        else content_request.get('output_config', {})

        # Stage 1: Quiz generation
        if output_config.get('quiz', False):
            logger.info("=== STAGE 1: Quiz Generation ===")
            quiz_prompt = self.prompt_builder.build_quiz_prompt(content_request)

            await self._navigate_to_custom_report()
            await self._send_prompt(quiz_prompt)
            quiz_content = await self._extract_response()

            results['quiz_csv'] = quiz_content
            logger.info(f"✓ Quiz generated ({len(quiz_content)} chars)")

        # Stage 2: Study guide
        if output_config.get('studyGuide', False):
            logger.info("=== STAGE 2: Study Guide Generation ===")
            guide_prompt = self.prompt_builder.build_study_guide_prompt(content_request)

            await self._navigate_to_custom_report()
            await self._send_prompt(guide_prompt)
            guide_content = await self._extract_response()

            results['study_guide_md'] = guide_content
            logger.info(f"✓ Study guide generated ({len(guide_content)} chars)")

        # Stage 3: Visuals/Handout
        if output_config.get('handout', False):
            logger.info("=== STAGE 3: Handout/Visuals Generation ===")
            visual_prompt = self.prompt_builder.build_handout_prompt(content_request)

            await self._navigate_to_custom_report()
            await self._send_prompt(visual_prompt)
            visual_content = await self._extract_response()

            results['visuals_md'] = visual_content
            logger.info(f"✓ Handout generated ({len(visual_content)} chars)")

        logger.info(f"Multi-stage generation complete: {len(results)} artifacts created")
        return results

    async def _navigate_to_custom_report(self):
        """
        Navigate to "Notebook guide" → "Create Your Own".

        Based on lines 400-434 logic from current notebooklm.py.

        Raises:
            RuntimeError if navigation fails
        """
        logger.debug("Navigating to Notebook guide → Custom report...")

        try:
            # Click "Notebook guide" or "Reports"
            logger.debug("Looking for 'Notebook guide' button...")
            guide_btn = self.page.locator("button, [role='button']").filter(
                has_text=re.compile(r"Notebook guide|Reports", re.I)
            ).last

            if await guide_btn.is_visible(timeout=5000):
                await guide_btn.click(force=True)
                await self.page.wait_for_timeout(400)
                logger.debug("Clicked 'Notebook guide' button")
            else:
                logger.warning("'Notebook guide' button not visible, continuing...")

            # Click "Create Your Own" card
            logger.debug("Looking for 'Create Your Own' component...")
            create_own_card = self.page.locator(
                "report-customization-tile, .report-customization-tile"
            ).filter(has_text=re.compile(r"Create Your Own", re.I)).last

            if await create_own_card.is_visible(timeout=5000):
                logger.debug("Found 'Create Your Own' component, clicking...")
                await create_own_card.click(force=True)
                await self.page.wait_for_timeout(800)
            else:
                # Fallback: try any button/card with "Create" or "Custom"
                logger.debug("Trying fallback selector for custom report...")
                custom_card = self.page.locator("button, div[role='button']").filter(
                    has_text=re.compile(r"Create|Custom", re.I)
                ).first

                if await custom_card.is_visible(timeout=3000):
                    await custom_card.click(force=True)
                    await self.page.wait_for_timeout(800)
                else:
                    logger.warning("Could not find 'Create Your Own' option")

            # Check for "Custom" or "Instructions" button (dialog opener)
            logger.debug("Looking for custom/instructions trigger...")
            custom_trigger = self.page.locator(
                "div[role='dialog'] button, [role='button']"
            ).filter(has_text=re.compile(r"Custom|instructions|Help me create", re.I)).last

            if await custom_trigger.is_visible(timeout=3000):
                await custom_trigger.click(force=True)
                await self.page.wait_for_timeout(400)
                logger.debug("Clicked custom instructions trigger")

            logger.debug("Navigation to custom report completed")

        except Exception as e:
            logger.error(f"Navigation error: {e}")
            # Continue anyway - prompt injection might still work

    async def _send_prompt(self, prompt: str):
        """
        Fill textarea with prompt and trigger generation.

        Based on lines 438-497 logic from current notebooklm.py.

        Args:
            prompt: The formatted prompt string

        Raises:
            RuntimeError if prompt cannot be sent
        """
        logger.debug(f"Sending prompt (length: {len(prompt)} chars)...")

        try:
            # Bring page to front (important for modal focus)
            await self.page.bring_to_front()

            # Wait for textarea in dialog
            logger.debug("Waiting for textarea to appear...")
            try:
                await self.page.wait_for_selector(
                    'div[role="dialog"] textarea, .cdk-overlay-pane textarea',
                    timeout=5000,
                    state="visible"
                )
                logger.debug("Textarea visible")
            except Exception as e:
                logger.warning(f"Timeout waiting for textarea: {e}")
                # Continue anyway

            # Find and fill textarea
            logger.debug("Looking for prompt input field...")
            prompt_input = self.page.locator(
                'div[role="dialog"] textarea, textarea[placeholder*="instructions"]'
            ).first

            if await prompt_input.is_visible(timeout=5000):
                await prompt_input.fill(prompt)
                await self.page.wait_for_timeout(500)
                logger.debug(f"Filled prompt input ({len(prompt)} chars)")
            else:
                logger.error("Prompt input field not visible!")
                raise RuntimeError("Could not find prompt textarea")

            # Click "Create" or "Generate" button
            logger.debug("Looking for 'Create'/'Generate' button...")
            create_btn = self.page.locator("button").filter(
                has_text=re.compile(r"Create|Generate", re.I)
            ).first

            if await create_btn.is_visible(timeout=5000):
                await create_btn.click(force=True)
                logger.info("✓ Prompt sent, waiting for generation...")

                # Wait for generation to complete
                # Use adaptive wait based on prompt length (longer prompts = longer generation)
                wait_time = min(20000, max(10000, len(prompt) * 2))  # 10-20 seconds
                await self.page.wait_for_timeout(wait_time)

            else:
                logger.error("Create/Generate button not visible!")
                # Try pressing Enter as fallback
                await self.page.keyboard.press("Enter")
                await self.page.wait_for_timeout(10000)
                logger.warning("Used Enter key as fallback for submission")

        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            raise RuntimeError(f"Failed to send prompt: {e}")

    async def _extract_response(self) -> str:
        """
        Scrape generated content from DOM.

        Returns:
            Generated content as string

        Raises:
            RuntimeError if content cannot be extracted
        """
        logger.debug("Extracting generated response...")

        try:
            # Wait for response to appear
            logger.debug("Waiting for response element...")
            try:
                await self.page.wait_for_selector(
                    '.model-response-text, [data-generated-content], .generated-content',
                    state='visible',
                    timeout=30000
                )
                logger.debug("Response element visible")
            except Exception as e:
                logger.warning(f"Timeout waiting for response: {e}")

            # Get last response (most recent generation)
            logger.debug("Querying response elements...")
            responses = await self.page.query_selector_all('.model-response-text')

            if responses and len(responses) > 0:
                # Get the last (most recent) response
                content = await responses[-1].inner_text()
                logger.info(f"✓ Extracted response (length: {len(content)} chars)")
                return content
            else:
                # Fallback: try broader selector
                logger.debug("Trying fallback selector for response...")
                fallback_response = await self.page.locator(
                    'div[class*="response"], div[class*="generated"]'
                ).last.inner_text()

                if fallback_response:
                    logger.info(f"✓ Extracted response via fallback ({len(fallback_response)} chars)")
                    return fallback_response
                else:
                    logger.error("No response content found!")
                    return ""

        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            return ""

    async def wait_for_generation_complete(self, timeout: int = 60000) -> bool:
        """
        Wait for generation to complete by monitoring UI state.

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            True if generation completed, False if timeout
        """
        logger.debug("Waiting for generation to complete...")

        try:
            # Look for "generating" indicator to disappear
            # Or "Stop generating" button to disappear
            stop_btn = self.page.locator("button").filter(
                has_text=re.compile(r"Stop generating", re.I)
            ).first

            # Wait for stop button to appear (generation started)
            if await stop_btn.is_visible(timeout=5000):
                logger.debug("Generation started (Stop button visible)")

                # Now wait for it to disappear (generation finished)
                await stop_btn.wait_for(state="hidden", timeout=timeout)
                logger.info("✓ Generation completed")
                return True
            else:
                logger.debug("No 'Stop generating' button found, assuming generation complete")
                return True

        except Exception as e:
            logger.warning(f"Error waiting for generation: {e}")
            return False
