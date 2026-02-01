import os
from playwright.async_api import async_playwright

async def launch_browser():
    # Parse HEADLESS env var, default to False (debugger friendly)
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    
    import logging
    logger = logging.getLogger(__name__)
    
    # Store browser data in a persistent directory
    # Default to project folder, but allow override for real Chrome profile
    # Force isolated profile to avoid conflicts with open Chrome instances
    # user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    user_data_dir = os.path.join(os.getcwd(), "outputs", "browser_data")
    
    os.makedirs(user_data_dir, exist_ok=True)

    logger.info(f"Launching persistent browser context (headless={headless}) at {user_data_dir}")
    playwright = await async_playwright().start()
    
    # launch_persistent_context returns the context directly
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless,
        slow_mo=50,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        accept_downloads=True,
        # Stealth args to bypass Google "Not Secure" detection
        args=[
            "--disable-blink-features=AutomationControlled",
        ],
        ignore_default_args=["--enable-automation"]
    )

    # In persistent context, the first page is usually automatically created
    if context.pages:
        page = context.pages[0]
    else:
        page = await context.new_page()

    # Browser object is not separate here, but we return None to maintain signature compatibility
    return playwright, None, context, page
