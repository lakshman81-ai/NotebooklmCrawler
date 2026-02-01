
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Mock environment if needed
if not os.getenv("CHROME_USER_DATA_DIR"):
    os.environ["CHROME_USER_DATA_DIR"] = str(PROJECT_ROOT / "outputs" / "browser_data")

from crawler.browser import launch_browser

async def test_notebooklm_access():
    print(">>> Starting NotebookLM DOM Test")
    print(f"Project Root: {PROJECT_ROOT}")
    
    playwright = None
    browser = None
    context = None
    page = None

    try:
        print("Initializing browser via crawler.browser.launch_browser...")
        playwright, browser, context, page = await launch_browser()
        
        print("Navigating to https://notebooklm.google.com/ ...")
        await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        title = await page.title()
        print(f"Page Title: {title}")
        
        # Check login state
        if "Sign in" in title or "Try NotebookLM" in await page.content():
             print("!!! STATUS: NOT LOGGED IN")
             print("Please log in manually in the opened browser window if visible, or run with HEADLESS=false.")
             # We can't proceed with functional testing if not logged in
             return False
        else:
             print("STATUS: Logged in (likely)")
        
        # Check for Create/New Notebook button
        print("Checking for 'New notebook' or 'Create' button...")
        try:
            # Try a few selectors
            await page.wait_for_selector("text=New notebook", timeout=5000)
            print("SUCCESS: Found 'New notebook' button.")
        except:
             try:
                 await page.wait_for_selector("button[aria-label*='Create']", timeout=5000)
                 print("SUCCESS: Found 'Create' button.")
             except:
                 print("WARNING: Could not find 'New notebook' or 'Create' button. Might be on a specific notebook page or UI changed.")
                 await page.screenshot(path="test_notebooklm_ui_unknown.png")
        
        print(">>> Test Passed (Basic Access)")
        return True

    except Exception as e:
        print(f"!!! Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("Cleaning up resources...")
        if context: await context.close()
        if browser: await browser.close()
        if playwright: await playwright.stop()

if __name__ == "__main__":
    asyncio.run(test_notebooklm_access())
