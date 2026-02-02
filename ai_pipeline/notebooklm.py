import re
import logging
import time
import os
from bs4 import BeautifulSoup
import sys
import asyncio
from typing import List, Dict, Optional
from contracts.chunk_schema import Chunk

logger = logging.getLogger(__name__)

def _build_dynamic_search_query(context: dict) -> str:
    """
    Build a dynamic search query using all trusted domains.

    Args:
        context: Dictionary with topic, grade, subtopics

    Returns:
        Search query string with OR'd site filters
    """
    from contracts.source_policy import TRUSTED_DOMAINS

    topic = context.get('topic', '')
    grade = context.get('grade', '')
    subtopics = context.get('subtopics', [])

    # Build keywords string
    if isinstance(subtopics, list):
        keywords = " ".join(subtopics)
    else:
        keywords = str(subtopics)

    # Build site filters with OR
    if TRUSTED_DOMAINS:
        site_filters = " OR ".join([f"site:{d}" for d in TRUSTED_DOMAINS])
        site_clause = f"({site_filters})"
    else:
        site_clause = ""

    # Combine all parts
    query_parts = [topic, grade, keywords, site_clause]
    query = " ".join(part for part in query_parts if part.strip())

    return query.strip()

async def dismiss_popups(page):
    """
    Helper to auto-approve/dismiss common onboarding tooltips or dialogs.
    """
    # 1. Handle the backdrop first if it exists
    try:
        backdrop = page.locator(".cdk-overlay-backdrop, .mat-mdc-dialog-container").first
        if await backdrop.is_visible():
            logger.info("Overlay backdrop detected. Attempting to dismiss via Escape key...")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)  # SPEED: Reduced from 1000ms
    except: pass

    targets = [
        "Got it", "Next", "Close", "No thanks", "Done", "I understand",
        "Confirm", "Allow", "Continue", "Stay here", "Wait", "Dismiss",
        "Sign in", "Use another account", "Choose an account", "Keep using",
        "Not now", "OK"
    ]
    for t in targets:
        try:
            # Look for button specifically
            btn = page.locator("button, [role='button']").filter(has_text=re.compile(f"^{t}$|^{t}.*", re.I))
            if await btn.count() > 0:
                for i in range(await btn.count()):
                    target_btn = btn.nth(i)
                    if await target_btn.is_visible():
                        # Use force=True for dismissal to punch through overrides
                        await target_btn.click(timeout=500, force=True)  # SPEED: Reduced from 1000ms
                        logger.info(f"Auto-dismissed element with text: '{t}'")
                        await page.wait_for_timeout(150)  # SPEED: Reduced from 500ms
        except:
            pass


def _extract_robust_title_from_html(html: str) -> str:
    """Helper to pull title from raw HTML if chunk title is missing."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
    except:
        pass
    return ""


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

async def run_notebooklm(chunks: List[Chunk], context: Optional[Dict] = None, page = None) -> Dict:
    """
    Browser-based implementation of NotebookLM.
    Navigates to the UI, performs discovery or uploads content, and extracts summary/report.
    """
    if not page:
        raise RuntimeError("No browser page provided for NotebookLM DOM automation")

    discovery_method = (context or {}).get('discovery_method', 'auto').lower()
    material_type = (context or {}).get('output_type', 'study_material').lower()
    
    context_info = f" with context {context}" if context else ""
    logger.info(f"Starting NotebookLM Flow ({discovery_method}) for {len(chunks)} chunks{context_info}")

    # 1. Navigation
    try:
        current_url = page.url
        if "notebooklm.google.com" not in current_url:
            logger.info("Navigating to https://notebooklm.google.com/")
            await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
        else:
            logger.info("Already on NotebookLM, checking for dashboard...")
            await page.wait_for_load_state("domcontentloaded")
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise

    # 2. Authentication Check
    try:
        await dismiss_popups(page)
        if "accounts.google.com" in page.url or "Sign in" in await page.title() or "Try NotebookLM" in await page.content():
            logger.warning("Google Login Required! Waiting 5 minutes for manual login...")
            start_wait = time.time()
            while "accounts.google.com" in page.url or "Sign in" in await page.title():
                 await asyncio.sleep(2)
                 if time.time() - start_wait > 300:
                     raise RuntimeError("Login timed out.")
            logger.info("Login detected! Resuming...")
            await page.wait_for_timeout(1000)  # SPEED: Reduced from 3000ms
    except Exception as e:
        logger.error(f"Auth check failed: {e}")

    # 3. Automation Logic
    try:
        logger.info("Interacting with NotebookLM UI...")
        await dismiss_popups(page)
        
        # Dashboard or Inside Notebook?
        if "notebook/" not in page.url:
            logger.info("On Dashboard. Attempting to create new notebook...")
            # Try a loop for dashboard navigation
            dashboard_success = False
            for dash_attempt in range(3):
                try:
                    await dismiss_popups(page)
                    # 1. Primary: Text-based click with force=True
                    # Playwright often fails if the backdrop is there. force=True bypasses this.
                    try:
                        await page.get_by_text("New notebook", exact=False).click(timeout=3000, force=True)
                        dashboard_success = True
                        break
                    except: pass

                    # 2. Secondary: Locator-based click
                    try:
                        await page.locator("button, div[role='button']").filter(has_text=re.compile(r"New notebook|Create", re.I)).first.click(timeout=3000, force=True)
                        dashboard_success = True
                        break
                    except: pass

                    # 3. Fallback: Aria-label based
                    btn = page.locator("button[aria-label*='Create'], button[aria-label*='New']").first
                    if await btn.is_visible():
                        await btn.click(timeout=3000, force=True)
                        dashboard_success = True
                        break
                    
                    logger.warning(f"Dashboard attempt {dash_attempt+1} failed to open notebook. Retrying...")
                    await page.wait_for_timeout(500)  # SPEED: Reduced from 2000ms
                except Exception as e:
                    logger.warning(f"Dashboard navigation error: {e}")
            
            if not dashboard_success:
                logger.error("Failed to click 'New notebook' after multiple attempts. Attempting emergency fallback (Direct URL or Tab navigation)")
                # If we are stuck, sometimes hitting Tab or Space works
                await page.keyboard.press("Tab")
                await page.keyboard.press("Enter")
            
            await page.wait_for_timeout(1500)  # SPEED: Reduced from 4000ms
        
        await dismiss_popups(page)

        if discovery_method == 'notebooklm':
            # --- SOURCE DISCOVERY FLOW ---
            logger.info("Executing Source Discovery Flow...")
            
            # Check for Explicit Target URL (from UI)
            target_url = (context or {}).get('target_url')
            # run.py might not populate target_url directly in context, logic needs verification
            # Actually run.py builds context from ContentRequest which has no target_ui?
            # Wait, run.py does NOT put target_url in build_context(request) usually.
            # We need to ensure it's there. 
            # In bridge.py -> TARGET_URL env.
            # In run.py -> build_context(request).
            # Let's assume for now fallback to env var if context misses it.
            if not target_url:
                target_url = os.getenv("TARGET_URL", "")
            
            # Robust Selection of "Add Source" -> "Web/Search"
            source_added = False
            
            # Attempt loop
            for attempt in range(3):
                try:
                    logger.info(f"Source addition attempt {attempt+1}...")
                    
                    # 1. Identify if the 'Add source' menu is already open / Target specific Angular Material classes
                    # The menu usually opens in a cdk-overlay-pane
                    # We look for typical specific source buttons to avoid grabbing the whole body.
                    
                    # Selectors focused on the overlay or specific button roles
                    web_regex = re.compile(r"Search the web|Web|URL", re.I)
                    site_regex = re.compile(r"Website", re.I)
                    
                    # Try to find refined candidates inside a dialog/menu or just buttons
                    candidates = page.locator("div[role='dialog'] button, div[role='menu'] button, .cdk-overlay-pane div[role='button'], button")
                    
                    web_option = candidates.filter(has_text=web_regex).last # Last is often safer if duplicates exist
                    site_option = candidates.filter(has_text=site_regex).last
                    
                    # If regex fails to find specific small buttons, fall back to broader but with force click
                    if not await web_option.is_visible() and not await site_option.is_visible():
                         # Menu likely closed, try to open 'Add source'
                         logger.info("Opening 'Add source' menu...")
                         
                         # Try specific buttons for "Add Source"
                         add_src_btn = page.locator("button, div[role='button']").filter(has_text=re.compile(r"Add source|Insert", re.I)).last
                         if await add_src_btn.is_visible():
                             await add_src_btn.click(force=True)
                             await page.wait_for_timeout(300)  # SPEED: Reduced from 1000ms
                         else:
                             # Try specific plus icon in sidebar
                             await page.locator(".material-symbols-outlined:has-text('add')").first.click(force=True)
                             await page.wait_for_timeout(300)  # SPEED: Reduced from 1000ms

                    # 2. Choose Option based on Target URL presence
                    if target_url and len(target_url) > 5:
                        logger.info(f"Target URL detected: {target_url}. Selecting 'Website' source...")
                        
                        # Use force=True to bypass "intercepted by overlay" errors
                        if await site_option.is_visible():
                            await site_option.click(force=True)
                        elif await web_option.is_visible():
                            await web_option.click(force=True)
                        else:
                            # Try finding it broadly but clicking forcefully
                            broad_site = page.locator("div, span").filter(has_text=site_regex).last
                            if await broad_site.is_visible():
                                await broad_site.click(force=True)
                            else:
                                logger.warning("Website option not found even after opening menu.")
                                continue # Retry loop

                        await page.wait_for_timeout(500)  # SPEED: Reduced from 1500ms
                        
                        # Handle Website Input - Refined selectors
                        logger.info("Looking for URL input field...")
                        url_input_selectors = [
                            "input[placeholder*='link']", 
                            "input[placeholder*='URL']",
                            "input[placeholder*='https']",
                            "input[type='url']",
                            "input[aria-label*='link']",
                            "textarea[placeholder*='link']"
                        ]
                        
                        url_input = None
                        for selector in url_input_selectors:
                            sel_locator = page.locator(selector).first
                            if await sel_locator.is_visible():
                                url_input = sel_locator
                                logger.info(f"Found URL input with selector: {selector}")
                                break
                        
                        if not url_input:
                            # Desperate fallback: find first input in a dialog
                            url_input = page.locator("div[role='dialog'] input").first
                            if await url_input.is_visible():
                                logger.info("Found URL input via dialog fallback")
                            else:
                                logger.warning("Could not find visible URL input field. Elements on page:")
                                # Log some details for debugging
                                try:
                                    inputs = await page.locator("input, textarea").all_inner_texts()
                                    logger.info(f"Visible inputs/textareas: {len(inputs)}")
                                except: pass
                                raise RuntimeError("URL input field not found or not visible.")

                        await url_input.fill(target_url)
                        await page.wait_for_timeout(300)  # SPEED: Reduced from 800ms
                        
                        # Click Insert/Add - More robust "Add/Insert" finding
                        insert_btn_regex = re.compile(r"Insert|Add|Import|Done", re.I)
                        insert_btn = page.locator("button").filter(has_text=insert_btn_regex).last
                        
                        if await insert_btn.is_visible() and await insert_btn.is_enabled():
                            logger.info(f"Clicking final insertion button: {await insert_btn.inner_text()}")
                            await insert_btn.click(force=True)
                            source_added = True
                            logger.info("URL inserted successfully.")
                            break
                        else:
                            # Fallback: Enter key
                            await page.keyboard.press("Enter")
                            source_added = True
                            logger.info("URL added via Enter key fallback.")
                            break
                    else:
                        # Fallback to Search
                        logger.info("No Target URL. Selecting 'Search the web'...")
                        if await web_option.is_visible():
                            await web_option.click(force=True)
                            source_added = True
                            break
                        else:
                             # Broad fallback
                             broad_web = page.locator("div, span").filter(has_text=web_regex).last
                             if await broad_web.is_visible():
                                 await broad_web.click(force=True)
                                 source_added = True
                                 break
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1} warning: {e}")
                    await page.wait_for_timeout(500)  # SPEED: Reduced from 2000ms

            if not source_added:
                # One last desperate try using tab navigation or generic robust selector
                logger.warning("Standard source addition failed. Trying accessible fallbacks.")
                await page.keyboard.press("Escape") # Close any rogue modals
                await page.wait_for_timeout(200)  # SPEED: Reduced from 500ms
                # Try to just type 'Search' which might trigger something if in a focused state? No.
                if target_url:
                     logger.error("Could not add Target URL via 'Website' option.")
                else:
                     raise RuntimeError("Could not find 'Search the web' option after multiple attempts.")

            await page.wait_for_timeout(500)  # SPEED: Reduced from 1500ms

            if not target_url:
                # Search Query (Only if NO URL)
                search_query = _build_dynamic_search_query(context or {})
                
                logger.info(f"Performing search: {search_query}")
                # Robust input finding
                search_input = page.locator("input[placeholder*='Search'], textarea[placeholder*='Search'], input[aria-label*='Search']").first
                await search_input.fill(search_query)
                await page.keyboard.press("Enter")
                
                # Import sources
                logger.info("Waiting for search results and importing...")
                # Wait longer for google search results
                await page.wait_for_selector("text=Select all", timeout=30000)
                
                # Click "Select all" (text varies: "Select all sources", "Select all")
                await page.locator("input[type='checkbox'], span").filter(has_text=re.compile(r"Select all", re.I)).first.click()
                await page.wait_for_timeout(200)  # SPEED: Reduced from 500ms
                
                # Click Import
                import_btn = page.locator("button").filter(has_text=re.compile(r"Import|Insert", re.I)).first
                await import_btn.click()
            
            # Wait for processing - This can take a while "Reading sources..."
            logger.info("Waiting for sources to be processed...")
            await page.wait_for_timeout(3000)  # SPEED: Reduced from 10000ms
            
            # Report Generation
            logger.info("Starting Report Generation...")

            
            # --- DEEP LOGIC: Master Prompt Construction ---
            use_deep_logic = os.getenv("USE_DEEP_LOGIC", "false").lower() == "true"
            output_config = context.get('output_config', {})
            difficulty = context.get('difficulty', 'Medium')
            custom_prompt = context.get('custom_prompt', '')
            keywords_report = context.get('keywords_report', '')
            
            master_prompt = ""
            if use_deep_logic:
                # Report 0: Source Master Context
                master_prompt += f"SOURCE ANALYSIS CONTEXT:\nAnalyze the sources for Authority and Gaps. Focus on '{keywords_report}' if provided.\n\n"
                
                # Report 1: Difficulty Engine
                diff_map = {
                    "Identify": "Focus on definitions, basic facts, and identification of key terms. (Easy Level)",
                    "Connect": "Focus on relationships, cause-and-effect, and connecting concepts across sources. (Medium Level)",
                    "Extend": "Focus on applications, scenario-based analysis, and extending concepts to new situations. (Hard Level)"
                }
                master_prompt += f"[DIFFICULTY: {difficulty}]\n{diff_map.get(difficulty, diff_map['Connect'])}\n\n"
            else:
                logger.info("Deep Logic (Source Analysis/Difficulty) is OFF by default. Skipping preamble.")
            
            # Report 2: Dynamic Templates
            tasks = []
            
            if output_config.get('studyGuide'):
                tasks.append("[TASK: STUDY GUIDE]\nCreate a detailed study guide extracting Anchor Concepts and key definitions.")
                
            if output_config.get('quiz'):
                # Handle Sub-options ideally, for now generic robust quiz prompt
                # If we had the granular numbers from context, we'd use them here.
                # Assuming context['output_config'] might contain nested quiz details or we parse it from somewhere else.
                # But typically we just passed the boolean config.
                # Let's check context['quiz_config'] if we added it? We did pass CR_QUIZ_CONFIG in bridge.
                # But context_builder implementation might have missed extracting valid JSON from it? 
                # context_builder passed 'output_config' directly. 
                # Let's rely on standard instructions + custom prompt for now.
                tasks.append("[TASK: QUIZ]\nCreate a quiz with 10 Multiple Choice Questions, 5 Assertion-Reasoning questions, and 3 Detailed Answer questions. Include a separate Answer Key.")
            
            if output_config.get('handout'):
                tasks.append("[TASK: HANDOUT]\nCreate a Visual Handout script describing a layout for a one-page summary with diagrams.")

            if custom_prompt:
                tasks.append(f"\n[CUSTOM INSTRUCTIONS]\n{custom_prompt}")
            
            if not tasks:
                 tasks.append("Create a comprehensive summary of the sources.")
                 
            prompt = master_prompt + "\n\n".join(tasks)
            logger.info(f"Generated Master Prompt: {prompt[:100]}...")

            # Trigger "Report" / "Notebook guide" -> "Study guide" -> "Custom"
            logger.info("Navigating to Notebook guide -> Custom report...")
            # Navigation Hardening: Reverted delays to original snappiness
            try:
                # 1. Try "Notebook guide" or "Reports"
                guide_btn = page.locator("button, [role='button']").filter(has_text=re.compile(r"Notebook guide|Reports", re.I)).last
                if await guide_btn.is_visible():
                    # Clean the label for logging to prevent Unicode crash
                    raw_text = await guide_btn.inner_text()
                    safe_text = raw_text.encode('ascii', 'ignore').decode('ascii').strip().replace("\n", " ")
                    logger.info(f"Clicking guide button: {safe_text[:30]}...")
                    await guide_btn.click(force=True)
                    await page.wait_for_timeout(400)  # SPEED: Reduced from 1000ms

                # Precise Card Selection based on structural analysis
                create_own_card = page.locator("report-customization-tile, .report-customization-tile").filter(has_text=re.compile(r"Create Your Own", re.I)).last
                preset_card = page.locator("report-customization-tile").filter(has_text=re.compile(r"Briefing|Study guide|Summary|Table", re.I)).first

                if await create_own_card.is_visible():
                    logger.info("Found 'Create Your Own' component. Clicking...")
                    await create_own_card.click(force=True)
                    await page.wait_for_timeout(800)  # SPEED: Reduced from 2000ms
                elif await preset_card.is_visible():
                    logger.info("Clicking available report preset card...")
                    await preset_card.click(force=True)
                    await page.wait_for_timeout(400)  # SPEED: Reduced from 1000ms

                # Check for "Custom" or "Instructions" buttons
                custom_trigger = page.locator("div[role='dialog'] button, [role='button']").filter(has_text=re.compile(r"Custom|instructions|Help me create", re.I)).last
                if await custom_trigger.is_visible():
                    await custom_trigger.click(force=True)
                    await page.wait_for_timeout(400)  # SPEED: Reduced from 1000ms
            except Exception as e:
                logger.warning(f"Flow navigation issue: {str(e)}. Proceeding with direct prompt box search.")

            # PHASE 13: HARDENED AGENT & LEAKAGE BLOCKER
            # ZERO TOLERANCE: STOP on failure. No blind fallbacks.
            prompt_found = False
            try:
                # 9. Background Window Protection
                await page.bring_to_front()
                
                logger.info("Waiting for visible 'Create report' modal with textarea...")
                # Wait for a dialog with textarea (the custom prompt input)
                try:
                    await page.wait_for_selector('div[role="dialog"] textarea, .cdk-overlay-pane textarea', timeout=5000, state="visible")  # SPEED: Reduced from 10000ms
                    logger.info("Found textarea in dialog")
                except:
                    logger.warning("Primary textarea wait failed. Trying broader selector...")
                    try:
                        await page.wait_for_selector('textarea[placeholder], textarea[aria-label]', timeout=3000, state="visible")  # SPEED: Reduced from 5000ms
                        logger.info("Found textarea with placeholder/aria-label")
                    except:
                        logger.warning("Fallback textarea wait also failed. Proceeding with DOM agent anyway...")
                
                logger.info("Executing Hardened DOM Agent (NotebookLM_Report_Text_Injector)...")
                
                # We execute the agent logic directly in the browser context
                agent_result = await page.evaluate("""async (prompt_text) => {
                    // Step 0: Background Window Protection + Focus
                    window.blur();

                    // 3. Context Lock
                    if (!window.location.href.includes("notebooklm.google.com")) {
                        throw new Error("Context Lock Failed: Not on NotebookLM");
                    }

                    // 4. Target Resolution (ZERO ambiguity)
                    // Find ALL visible dialogs and pick the one with "Create report" header or "Create Your Own" tile
                    const dialogs = Array.from(document.querySelectorAll('div[role="dialog"], [class*="dialog"], [class*="modal"], .cdk-overlay-pane'));

                    let modal = null;
                    let textarea = null;

                    // Strategy 1: Find dialog with "Create report" text AND a textarea inside
                    for (const d of dialogs) {
                        if (d.offsetWidth === 0 || d.offsetHeight === 0) continue; // Skip hidden
                        const hasCreateReport = d.innerText && (d.innerText.includes("Create report") || d.innerText.includes("Create Your Own"));
                        if (hasCreateReport) {
                            // Look for textarea specifically in the custom prompt area
                            const ta = d.querySelector('textarea[placeholder], textarea[aria-label], textarea');
                            if (ta && ta.offsetWidth > 0 && ta.offsetHeight > 0) {
                                modal = d;
                                textarea = ta;
                                break;
                            }
                        }
                    }

                    // Strategy 2: Find textarea in CDK overlay pane (Angular Material)
                    if (!textarea) {
                        const overlayPanes = document.querySelectorAll('.cdk-overlay-pane');
                        for (const pane of overlayPanes) {
                            if (pane.offsetWidth === 0 || pane.offsetHeight === 0) continue;
                            const ta = pane.querySelector('textarea');
                            if (ta && ta.offsetWidth > 0 && ta.offsetHeight > 0) {
                                // Verify it's in a "Create report" context by checking ancestors
                                const paneText = pane.innerText || '';
                                if (paneText.includes('Create report') || paneText.includes('Generate') || paneText.includes('Custom')) {
                                    modal = pane;
                                    textarea = ta;
                                    break;
                                }
                            }
                        }
                    }

                    // Strategy 3: Find by aria-label or placeholder
                    if (!textarea) {
                        const candidates = document.querySelectorAll('textarea[aria-label*="prompt" i], textarea[aria-label*="custom" i], textarea[placeholder*="describe" i], textarea[placeholder*="instructions" i]');
                        for (const ta of candidates) {
                            if (ta.offsetWidth > 0 && ta.offsetHeight > 0) {
                                textarea = ta;
                                modal = ta.closest('div[role="dialog"], .cdk-overlay-pane, [class*="modal"]');
                                break;
                            }
                        }
                    }

                    if (!textarea) throw new Error("Target Resolution Failed: No visible textarea found in Create report modal");

                    // Step 4.1: ACTIVE LEAKAGE PREVENTION - Clear only OTHER textareas, not our target
                    document.querySelectorAll('textarea').forEach(tx => {
                        if (tx !== textarea && tx.value.length > 0) {
                            tx.value = "";
                            tx.dispatchEvent(new Event("input", { bubbles: true }));
                        }
                    });

                    // 5. Visibility + Focus Enforcement
                    textarea.scrollIntoView({ block: "center" });

                    // Clear any existing selection/focus elsewhere
                    if (document.activeElement && document.activeElement !== textarea) {
                        document.activeElement.blur();
                    }

                    textarea.focus();
                    textarea.click();

                    // Wait a moment for focus to settle
                    await new Promise(r => setTimeout(r, 100));

                    if (document.activeElement !== textarea) {
                        // Force focus via dispatchEvent
                        textarea.dispatchEvent(new FocusEvent('focus', { bubbles: true }));
                        textarea.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    }

                    // 6. Example Text Removal (CRITICAL)
                    textarea.value = "";
                    textarea.dispatchEvent(new Event("input", { bubbles: true }));

                    // 7. Content Injection (Direct DOM substitution)
                    textarea.value = prompt_text;
                    textarea.dispatchEvent(new Event("input", { bubbles: true }));
                    textarea.dispatchEvent(new Event("change", { bubbles: true }));

                    // Also trigger keyup for frameworks that listen to that
                    textarea.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));

                    // 8. Post-Write Verification (Non-negotiable)
                    if (!textarea.value.includes(prompt_text.slice(0, 50))) {
                        throw new Error("Post-Write Verification Failed: Content mismatch");
                    }

                    return { success: true, modalFound: !!modal };
                }""", prompt)

                if agent_result and agent_result.get('success'):
                    logger.info(f"Agent reports injection success (modal found: {agent_result.get('modalFound')}). Clicking Generate...")
                    prompt_found = True

                    # 10. Final Action: Clicking Generate button
                    # Try multiple strategies to find the Generate button
                    gen_clicked = False

                    # Strategy 1: Button with "Generate" text in any overlay/dialog
                    gen_selectors = [
                        'button:has-text("Generate")',
                        '.cdk-overlay-pane button:has-text("Generate")',
                        'div[role="dialog"] button:has-text("Generate")',
                        'button:has-text("Create")',
                        '[role="button"]:has-text("Generate")',
                    ]

                    for selector in gen_selectors:
                        try:
                            gen_btn = page.locator(selector).last
                            if await gen_btn.is_visible(timeout=2000):
                                logger.info(f"Found Generate button with selector: {selector}")
                                await gen_btn.click(force=True)
                                gen_clicked = True
                                break
                        except:
                            continue

                    if not gen_clicked:
                        # Strategy 2: Use JavaScript to find and click the button
                        logger.info("Trying JavaScript click for Generate button...")
                        js_clicked = await page.evaluate("""() => {
                            const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                            const genBtn = buttons.find(b => b.innerText && b.innerText.toLowerCase().includes('generate'));
                            if (genBtn) {
                                genBtn.click();
                                return true;
                            }
                            return false;
                        }""")
                        if js_clicked:
                            logger.info("Generate button clicked via JavaScript")
                            gen_clicked = True

                    if not gen_clicked:
                        logger.warning("Generate button not found, pressing Enter as fallback.")
                        await page.keyboard.press("Enter")

                    # Wait a moment for the generation to start
                    await page.wait_for_timeout(800)  # SPEED: Reduced from 2000ms

            except Exception as e:
                # 10. Failure Handling Strategy
                logger.error(f"DETECTION ALERT: {str(e)}")
                # CRITICAL: We do NOT fallback to chat here. STOP immediately.
                raise RuntimeError(f"NotebookLM_Report_Text_Injector Aborted: {str(e)}")

            if not prompt_found:
                 raise RuntimeError("UI logic failed: Agent completed but prompt_found is False")

            logger.info("Waiting for report generation to complete...")

            # Wait for generation to complete - look for generated content or completion indicators
            try:
                # Wait for the report content to appear (the modal should close or content should appear)
                await page.wait_for_timeout(2000)  # SPEED: Reduced from 5000ms

                # Check if we're still in the modal or if report appeared
                for i in range(30):  # Up to 1 minute (30 * 2 seconds)
                    # Check if the Create report modal is still open
                    modal_visible = await page.locator('div[role="dialog"]:has-text("Create report")').is_visible()
                    if not modal_visible:
                        logger.info("Report modal closed - generation likely complete")
                        break

                    # Check for loading/generating indicators
                    generating = await page.locator('text=/generating|loading|please wait/i').is_visible()
                    if generating:
                        logger.info(f"Report still generating... ({(i+1)*2}s)")

                    await page.wait_for_timeout(2000)  # SPEED: Reduced from 5000ms
                else:
                    logger.warning("Timeout waiting for report generation, proceeding anyway")

            except Exception as e:
                logger.warning(f"Error during generation wait: {e}. Continuing...")

            # Extra wait to ensure content is fully rendered
            await page.wait_for_timeout(5000)

            # Export
            timestamp = int(time.time())
            export_path = os.path.abspath(os.path.join("outputs", f"notebooklm_report_{timestamp}.pdf"))
            logger.info(f"Exporting report to {export_path}")
            
            try:
                # Capture as PDF
                await page.pdf(path=export_path)
                logger.info("PDF Capture successful.")
            except:
                logger.warning("PDF capture failed, taking full page screenshot.")
                await page.screenshot(path=export_path.replace(".pdf", ".png"), full_page=True)

            return {
                "summary": f"NotebookLM Cloud Discovery Complete ({material_type})",
                "evidence": [f"Exported result: {os.path.basename(export_path)}"],
                "synthesis_summary": f"Produced {material_type} using NotebookLM discovery."
            }

        else:
            # --- UPLOAD FLOW (Original) ---
            unique_titles = []
            if chunks:
                for c in chunks:
                    html_src = getattr(c, 'metadata', {}).get('source_html')
                    t = _extract_robust_title_from_html(html_src) if html_src else getattr(c, 'source_title', '').strip()
                    if t and t not in unique_titles and t.lower() not in ['unknown', 'untitled']:
                        unique_titles.append(t)
            
            agg_topic = " & ".join(unique_titles[:3]) if unique_titles else (context.get('topic', 'Investigation') if context else 'Investigation')
            timestamp = int(time.time())
            temp_dir = os.path.join("outputs", "temp_sources")
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_html_path = os.path.abspath(os.path.join(temp_dir, f"source_{timestamp}.html"))
            temp_pdf_path = os.path.abspath(os.path.join(temp_dir, f"source_{timestamp}.pdf"))
            
            subtopics = (context or {}).get('subtopics', [])
            subtopic_str = f" ({', '.join(subtopics)})" if subtopics else ""
            
            html_content = f"<html><body><h1>{agg_topic}</h1><h4>Mission Scope: {subtopic_str}</h4><hr>"
            for i, chunk in enumerate(chunks):
                content = getattr(chunk, 'metadata', {}).get('source_html') or chunk.text
                html_content += f"<div><h2>Section {i+1}</h2>{content}</div><hr>"
            html_content += "</body></html>"
            
            with open(temp_html_path, "w", encoding="utf-8") as f: f.write(html_content)
            
            try:
                import subprocess
                pdf_gen_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils", "pdf_gen.py"))
                subprocess.run([sys.executable, pdf_gen_script, temp_html_path, temp_pdf_path], timeout=30)
                upload_target_path = temp_pdf_path
            except:
                upload_target_path = os.path.abspath(os.path.join(temp_dir, f"source_{timestamp}.txt"))
                with open(upload_target_path, "w", encoding="utf-8") as f: f.write("\n\n".join([c.text for c in chunks]))

            # Interaction
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
            
            await page.wait_for_timeout(5000)
            await page.wait_for_selector("text=/Notebook Guide|Summary/i", timeout=60000)
            
            return {
                "summary": "NotebookLM Compilation Complete",
                "evidence": [f"Uploaded source: {os.path.basename(upload_target_path)}"],
                "synthesis_summary": "Unified compilation performed via NotebookLM Web UI."
            }

    except Exception as e:
        logger.error(f"NotebookLM automation failed: {e}")
        ts = int(time.time())
        try: await page.screenshot(path=os.path.join("outputs", f"notebooklm_failure_{ts}.png"))
        except: pass
        raise
