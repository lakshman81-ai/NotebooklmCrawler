import re
import logging
import time
import os
import asyncio
from typing import List, Dict, Optional
from contracts.chunk_schema import Chunk
from prompt_modules.input_source_prompts import InputSourcePromptBuilder
from discovery.discovery_router import discover_urls
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def dismiss_popups(page):
    try:
        backdrop = page.locator(".cdk-overlay-backdrop, .mat-mdc-dialog-container").first
        if await backdrop.is_visible():
            logger.info("Overlay backdrop detected. Dismissing...")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
    except: pass

    # Common onboarding/popups
    targets = ["Got it", "Next", "Close", "No thanks", "Done", "I understand", "Confirm"]
    for t in targets:
        try:
            btn = page.locator("button, [role='button']").filter(has_text=re.compile(f"^{t}$|^{t}.*", re.I))
            if await btn.count() > 0:
                for i in range(await btn.count()):
                    target_btn = btn.nth(i)
                    if await target_btn.is_visible():
                        await target_btn.click(timeout=500, force=True)
                        await page.wait_for_timeout(150)
        except: pass

async def _find_upload_button(page):
    selectors = [
        "button:has-text('PDF')",
        "div[role='button']:has-text('PDF')",
        "button:has-text('Upload')",
        ".material-symbols-outlined:has-text('upload_file')",
        ".cdk-overlay-pane button:visible"
    ]
    for s in selectors:
        try:
            btn = page.locator(s).first
            if await btn.is_visible(timeout=1000): return btn
        except: pass
    return None

async def run_notebooklm(chunks: List[Chunk], context: Optional[Dict] = None, page = None) -> Dict:
    if not page: raise RuntimeError("No browser page provided")

    discovery_method = (context or {}).get('discovery_method', 'auto').lower()
    injection_mode = os.getenv("NOTEBOOKLM_INJECTION_MODE", "false").lower() == "true"
    
    logger.info(f"Starting NotebookLM Flow ({discovery_method}). Injection Mode: {injection_mode}")

    # 1. Navigation
    try:
        if "notebooklm.google.com" not in page.url:
            await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
        else:
            await page.wait_for_load_state("domcontentloaded")
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise

    # 2. Auth Check
    await dismiss_popups(page)
    if "accounts.google.com" in page.url or "Sign in" in await page.title():
        logger.warning("Google Login Required! Waiting up to 5 mins...")
        start_wait = time.time()
        while "accounts.google.com" in page.url:
            await asyncio.sleep(2)
            if time.time() - start_wait > 300: raise RuntimeError("Login timed out.")
        logger.info("Login detected! Resuming...")
        await page.wait_for_timeout(1000)

    # 3. Create/Open Notebook
    await dismiss_popups(page)
    if "notebook/" not in page.url:
        logger.info("Creating new notebook...")
        try:
            await page.get_by_text("New notebook", exact=False).click(timeout=5000)
        except:
            await page.locator("button, div[role='button']").filter(has_text="New notebook").click(force=True)
        await page.wait_for_timeout(3000)

    # 4. Source Logic (Auto Discovery or Direct URL)
    target_url = (context or {}).get('target_url') or os.getenv("TARGET_URL", "")

    if discovery_method == 'notebooklm':
        # Auto-Discovery fallback if no URL provided
        if not target_url:
            logger.info("No target URL provided. Initiating Auto-Discovery via SearchManager...")
            # Use PromptBuilder to generate search query
            builder = InputSourcePromptBuilder(
                grade=context.get('grade', 'General'),
                subject=context.get('subject', 'General'),
                topic=context.get('topic', 'Analysis'),
                difficulty=context.get('difficulty', 'Medium'),
                keywords=context.get('subtopics', [])
            )
            query = builder.generate_search_query()
            urls = await discover_urls(query, max_results=1) # Just get top 1 for now or list?
            if urls:
                target_url = urls[0]
                logger.info(f"Auto-Discovered URL: {target_url}")
            else:
                logger.warning("Auto-Discovery failed. Proceeding without specific source (Generic Report).")

        if target_url:
            logger.info(f"Adding Web Source: {target_url}")
            try:
                # Open "Add source" menu if needed
                add_btn = page.locator("button").filter(has_text="Add source").last
                if await add_btn.is_visible(): await add_btn.click()
                await page.wait_for_timeout(500)

                # Select "Website"
                src_btn = page.locator("button, div[role='button']").filter(has_text=re.compile(r"Website|Link", re.I)).last
                if await src_btn.is_visible():
                    await src_btn.click()
                    
                    # Input URL safely
                    inp = page.locator("input[placeholder*='link'], input[type='url']").first
                    await inp.fill(target_url)
                    await page.keyboard.press("Enter")
                    
                    logger.info("Waiting for source processing...")
                    await page.wait_for_timeout(8000) # Give it time to crawl
            except Exception as e:
                logger.warning(f"Source addition warning: {e}")

    # 5. Prompt Generation & Injection
    logger.info("Generating Prompt...")
    builder = InputSourcePromptBuilder(
        grade=context.get('grade', 'General'),
        subject=context.get('subject', 'General'),
        topic=context.get('topic', 'Analysis'),
        difficulty=context.get('difficulty', 'Medium'),
        keywords=context.get('subtopics', [])
    )

    # Correctly call the method to generate the full prompt text
    # Assuming output_config is part of context or needs extraction
    output_config = context.get('output_config') or context.get('outputs') or {}
    custom_prompt = context.get('custom_prompt', '')

    prompt_text = builder.generate_notebooklm_prompt(output_config, custom_prompt)
    logger.info(f"Prompt Generated (Length: {len(prompt_text)})")

    # Navigate to Chat
    try:
        await page.keyboard.press("Escape") # Close modals
        chat_box = page.locator("textarea[placeholder*='chat'], textarea[aria-label*='chat']").last

        if not await chat_box.is_visible():
            logger.warning("Chat box hidden. Trying to open via 'Notebook guide'...")
            guide_btn = page.locator("button").filter(has_text="Notebook guide").last
            if await guide_btn.is_visible(): await guide_btn.click()
            await page.wait_for_timeout(1000)

        if await chat_box.is_visible():
            await chat_box.click()
            
            if injection_mode:
                logger.info("Mode: DOM Injection (Fallback)")
                # Hardened Agent Logic (Restored)
                await page.evaluate("""(text) => {
                    const el = document.activeElement;
                    if (el && (el.tagName === 'TEXTAREA' || el.isContentEditable)) {
                        el.value = text;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    } else {
                        throw new Error("Active element is not a text input");
                    }
                }""", prompt_text) # Pass safely as arg
            else:
                logger.info("Mode: Clipboard Paste (Default)")
                # Clipboard Injection via JS (Safe Eval)
                await page.evaluate("text => navigator.clipboard.writeText(text)", prompt_text)
                
                await chat_box.focus()
                await chat_box.click()
                
                # Platform-specific modifier
                modifier = "Meta" if "Mac" in await page.evaluate("navigator.platform") else "Control"
                await page.keyboard.press(f"{modifier}+V")
                
                # Verification
                await page.wait_for_timeout(500)
                val = await chat_box.input_value()
                if not val:
                    logger.warning("Paste failed (empty). Fallback to fill.")
                    await chat_box.fill(prompt_text)

            # Submit
            await page.keyboard.press("Enter")
            
            # Wait for Generation
            logger.info("Waiting for response generation...")
            await page.wait_for_timeout(15000) # Initial wait
            
            # Export Screenshot
            timestamp = int(time.time())
            export_path = os.path.abspath(os.path.join("outputs", f"notebooklm_report_{timestamp}.png"))
            await page.screenshot(path=export_path, full_page=True)
            
            return {
                "summary": "NotebookLM Interaction Complete",
                "evidence": [f"Screenshot: {os.path.basename(export_path)}"]
            }
        else:
            raise RuntimeError("Chat box could not be found.")

    except Exception as e:
        logger.error(f"Interaction failed: {e}")
        raise

    return {}
