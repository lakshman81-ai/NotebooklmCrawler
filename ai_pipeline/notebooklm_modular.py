"""
NotebookLM Modular Integration

New modular prompt injection system that supports BOTH guided and unguided modes.
This is the refactored version using our new prompt modules.
"""

import re
import logging
import time
import os
import sys
import asyncio
from typing import List, Dict, Optional
from contracts.chunk_schema import Chunk

logger = logging.getLogger(__name__)

# Import dismiss_popups from the original module
from ai_pipeline.notebooklm import dismiss_popups


async def _find_upload_button(page):
    """
    Multi-strategy fallback to find the PDF/file upload button.
    Returns a locator for the button, or None if not found.

    Strategies (in order):
    1. Specific "PDF" button with regex
    2. Generic "File"/"Source"/"Upload" buttons
    3. Material Design upload icons
    4. First visible button in dialog/overlay pane
    """
    logger.info("Searching for upload button using multi-strategy approach...")

    # Strategy 1: Specific PDF button
    try:
        pdf_regex = re.compile(r"PDF", re.I)
        candidates = page.locator("button, div[role='button'], [role='button']")
        pdf_btn = candidates.filter(has_text=pdf_regex).first
        if await pdf_btn.is_visible(timeout=1000):
            logger.info("Found button using Strategy 1 (PDF button)")
            return pdf_btn
    except:
        pass

    # Strategy 2: Generic upload buttons
    try:
        upload_regex = re.compile(r"File|Source|Upload", re.I)
        candidates = page.locator("button, div[role='button']")
        upload_btn = candidates.filter(has_text=upload_regex).first
        if await upload_btn.is_visible(timeout=1000):
            logger.info("Found button using Strategy 2 (Generic upload keywords)")
            return upload_btn
    except:
        pass

    # Strategy 3: Material Design icons
    try:
        icon_selectors = [
            ".material-symbols-outlined:has-text('upload_file')",
            ".material-symbols-outlined:has-text('upload')",
            ".material-icons:has-text('upload_file')",
            "span[class*='material']:has-text('upload')"
        ]
        for selector in icon_selectors:
            icon_btn = page.locator(selector).first
            if await icon_btn.is_visible(timeout=500):
                logger.info(f"Found button using Strategy 3 (Material icon: {selector})")
                return icon_btn
    except:
        pass

    # Strategy 4: First button in dialog/overlay
    try:
        dialog_btn = page.locator(
            "div[role='dialog'] button:visible, "
            ".cdk-overlay-pane button:visible"
        ).first
        if await dialog_btn.is_visible(timeout=1000):
            logger.info("Found button using Strategy 4 (First visible button in dialog)")
            return dialog_btn
    except:
        pass

    logger.warning("No suitable upload button found via any strategy")
    return None


async def run_notebooklm_modular(chunks: List[Chunk], context: Optional[Dict] = None, page = None) -> Dict:
    """
    Unified NotebookLM automation with modular prompt injection system.

    Supports BOTH guided and unguided modes via NOTEBOOKLM_GUIDED environment variable.

    Args:
        chunks: List of Chunk objects (used in UNGUIDED mode)
        context: ContentRequest context dictionary
        page: Playwright Page object

    Returns:
        Dictionary with status, mode, and generated artifacts
    """
    if not page:
        raise RuntimeError("No browser page provided for NotebookLM DOM automation")

    # Import our new modular components
    from prompt_modules import PromptOrchestrator, InputSourcePromptBuilder
    from ai_pipeline.input_source_injector import InputSourcePromptInjector
    from ai_pipeline.output_prompt_injector import OutputPromptInjector

    # Determine mode
    guided_mode = os.getenv("NOTEBOOKLM_GUIDED", "false").lower() == "true"

    logger.info("========================================")
    logger.info("NotebookLM Modular System")
    logger.info(f"Mode: {'GUIDED' if guided_mode else 'UNGUIDED'}")
    logger.info(f"Chunks: {len(chunks)}")
    logger.info("========================================")

    try:
        # 1. Navigation & Authentication (reuse existing logic)
        current_url = page.url
        if "notebooklm.google.com" not in current_url:
            logger.info("Navigating to https://notebooklm.google.com/")
            await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
        else:
            logger.info("Already on NotebookLM")
            await page.wait_for_load_state("domcontentloaded")

        # 2. Auth check
        await dismiss_popups(page)
        if "accounts.google.com" in page.url or "Sign in" in await page.title():
            logger.warning("Google Login Required! Waiting up to 5 minutes...")
            start_wait = time.time()
            while "accounts.google.com" in page.url or "Sign in" in await page.title():
                await asyncio.sleep(2)
                if time.time() - start_wait > 300:
                    raise RuntimeError("Login timed out.")
            logger.info("✓ Login detected!")
            await page.wait_for_timeout(1000)

        # 3. Dashboard navigation
        await dismiss_popups(page)
        if "notebook/" not in page.url:
            logger.info("On Dashboard - creating new notebook...")
            for attempt in range(3):
                try:
                    await page.get_by_text("New notebook", exact=False).click(timeout=3000, force=True)
                    break
                except:
                    if attempt == 2:
                        await page.keyboard.press("Tab")
                        await page.keyboard.press("Enter")
            await page.wait_for_timeout(1500)

        await dismiss_popups(page)

        # ========================================================================
        # PHASE 1: INPUT SOURCE HANDLING (MODE-SPECIFIC)
        # ========================================================================

        if guided_mode:
            logger.info("=== PHASE 1: GUIDED MODE - Input Source Prompt Injection ===")

            # Initialize InputSourcePromptBuilder
            input_prompt_builder = InputSourcePromptBuilder(
                grade=context.get('grade', 'General'),
                subject=context.get('topic', '').split()[0] if context.get('topic') else 'General',
                topic=context.get('topic', ''),
                difficulty=context.get('difficulty', 'Medium'),
                keywords=context.get('subtopics', [])
            )

            # Initialize InputSourcePromptInjector
            input_injector = InputSourcePromptInjector(page, input_prompt_builder)

            # Get target URL
            target_url = context.get('target_url') or os.getenv("TARGET_URL", "")

            # Inject source discovery prompts
            success = await input_injector.inject_source_discovery_prompts(
                content_request=context,
                target_url=target_url if target_url else None
            )

            if not success:
                logger.warning("Source addition had issues, but continuing...")

            # Wait for source processing
            logger.info("Waiting for source processing...")
            await page.wait_for_timeout(5000)

        else:
            logger.info("=== PHASE 1: UNGUIDED MODE - Direct Upload ===")

            # Use existing upload flow
            timestamp = int(time.time())
            temp_dir = os.path.join("outputs", "temp")
            os.makedirs(temp_dir, exist_ok=True)

            temp_html_path = os.path.abspath(os.path.join(temp_dir, f"source_{timestamp}.html"))
            temp_pdf_path = os.path.abspath(os.path.join(temp_dir, f"source_{timestamp}.pdf"))

            # Generate HTML from chunks
            html_content = "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>"
            for i, chunk in enumerate(chunks):
                content = getattr(chunk, 'metadata', {}).get('source_html') or chunk.text
                html_content += f"<div><h2>Section {i+1}</h2>{content}</div><hr>"
            html_content += "</body></html>"

            with open(temp_html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Try PDF conversion, fallback to TXT
            try:
                import subprocess
                pdf_gen_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils", "pdf_gen.py"))
                subprocess.run([sys.executable, pdf_gen_script, temp_html_path, temp_pdf_path], timeout=30)
                upload_target_path = temp_pdf_path
            except:
                upload_target_path = os.path.abspath(os.path.join(temp_dir, f"source_{timestamp}.txt"))
                with open(upload_target_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join([c.text for c in chunks]))

            # Upload file
            logger.info(f"Uploading file: {upload_target_path}")
            await dismiss_popups(page)
            try:
                await page.get_by_role("button", name="Upload a source").click(timeout=3000)
            except:
                await page.locator("button").filter(has_text=re.compile(r"Add sources", re.I)).first.click(timeout=3000)

            await page.wait_for_timeout(1000)
            async with page.expect_file_chooser(timeout=10000) as fc_info:
                upload_btn = await _find_upload_button(page)
                if upload_btn:
                    await upload_btn.click(force=True)
                else:
                    # Emergency fallback to original selector
                    logger.warning("Falling back to original simple selector")
                    await page.locator("button:has-text('PDF'), div[role='button']:has-text('PDF')").first.click()
                await (await fc_info.value).set_files(upload_target_path)

            logger.info("File uploaded, waiting for processing...")
            await page.wait_for_timeout(8000)

        # ========================================================================
        # PHASE 2: OUTPUT GENERATION (SAME FOR BOTH MODES)
        # ========================================================================

        logger.info("=== PHASE 2: Output Prompt Injection (Quiz/Study/Handout) ===")

        # Initialize PromptOrchestrator
        prompt_orchestrator = PromptOrchestrator(context)

        # Initialize OutputPromptInjector
        output_injector = OutputPromptInjector(page, prompt_orchestrator)

        # Inject prompts and extract results
        results = await output_injector.inject_multi_stage_prompts(context)

        logger.info(f"✓ Output generation complete: {list(results.keys())}")

        # ========================================================================
        # RETURN RESULTS
        # ========================================================================

        return {
            "status": "success",
            "mode": "guided" if guided_mode else "unguided",
            "artifacts": results,
            "summary": f"NotebookLM modular generation complete ({len(results)} artifacts)",
            "evidence": list(results.keys())
        }

    except Exception as e:
        logger.error(f"NotebookLM modular automation failed: {e}")
        ts = int(time.time())
        try:
            await page.screenshot(path=os.path.join("outputs", f"notebooklm_modular_failure_{ts}.png"))
        except:
            pass
        raise
