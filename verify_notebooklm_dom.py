
import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Mock environment if needed to ensure we use the persistent profile
if not os.getenv("CHROME_USER_DATA_DIR"):
    # Default to project-local browser data if not set
    os.environ["CHROME_USER_DATA_DIR"] = str(PROJECT_ROOT / "outputs" / "browser_data")

# Force HEADLESS=false for verification so user can see/login
os.environ["HEADLESS"] = "false"

from crawler.browser import launch_browser

async def verify_notebooklm():
    print(">>> Starting NotebookLM DOM Verification")
    print(f"User Data Dir: {os.environ['CHROME_USER_DATA_DIR']}")
    
    playwright = None
    browser = None
    context = None
    page = None

    try:
        print("Initializing browser (Visible Mode)...")
        playwright, browser, context, page = await launch_browser()
        
        print("Navigating to https://notebooklm.google.com/ ...")
        # Increase timeout for potential login redirects
        await page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)
        
        title = await page.title()
        print(f"Page Title: {title}")
        
        # Check login state
        if "Sign in" in title or "Try NotebookLM" in await page.content():
             print("\n" + "!"*50)
             print(" ACTION REQUIRED: YOU ARE NOT LOGGED IN")
             print("!"*50)
             print("The browser window should be open.")
             print("Please log in to your Google Account manually in the window.")
             print("Waiting 120 seconds for you to log in...")
             
             # Wait for user to log in
             try:
                 # Check every 5 seconds if title changes
                 for i in range(24):
                     await asyncio.sleep(5)
                     title = await page.title()
                     if "Sign in" not in title and "NotebookLM" in title:
                         print("Login detected!")
                         break
             except KeyboardInterrupt:
                 print("Verification aborted by user.")
                 return

        # Re-check title
        title = await page.title()
        if "Sign in" in title:
            print("❌ Verification Failed: Context is still not logged in.")
            return

        print("✅ Status: Logged in.")
        
        # Check for Create/New Notebook button
        print("Checking for NotebookLM UI elements...")
        try:
            # Try a few selectors
            found = False
            for selector in ["text=New notebook", "button[aria-label*='Create']", "text=Add source"]:
                try:
                    if await page.is_visible(selector):
                        print(f"✅ Found UI Element: {selector}")
                        found = True
                        break
                except:
                    pass
            
            if not found:
                 print("⚠️  Warning: specific UI buttons not found. You might be inside a notebook already.")
                 
            await page.screenshot(path="notebooklm_verification_success.png")
            print("Snapshot saved to 'notebooklm_verification_success.png'")
            
        except Exception as e:
             print(f"❌ Error checking UI: {e}")
        
        print(">>> Verification Complete")

    except Exception as e:
        print(f"❌ Verification Logic Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Closing browser in 5 seconds...")
        await asyncio.sleep(5)
        if context: await context.close()
        if browser: await browser.close()
        if playwright: await playwright.stop()

if __name__ == "__main__":
    asyncio.run(verify_notebooklm())
