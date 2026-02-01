import asyncio
import os
import sys
import logging
from playwright.async_api import async_playwright

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_pipeline.notebooklm import run_notebooklm
from contracts.chunk_schema import Chunk

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

async def run_interactive_test():
    logger.info("Starting Interactive NotebookLM Test...")
    
    # 1. Create Dummy Data
    chunks = [
        Chunk(
            chunk_id=1,
            source_heading="Force and Pressure",
            text="# Force and Pressure\n\nForce is a push or a pull.",
            token_estimate=50,
            metadata={"source_html": "<h1>Force and Pressure</h1><p>Force is a <b>push</b> or a <b>pull</b>.</p><img src='https://via.placeholder.com/150' alt='Force Image'>"}
        ),
        Chunk(
            chunk_id=2,
            source_heading="Friction",
            text="## Friction\n\nFriction opposes motion.",
            token_estimate=50,
            metadata={"source_html": "<h2>Friction</h2><p>Friction <i>opposes</i> motion.</p>"}
        )
    ]
    
    context = {
        "grade": "Grade 8",
        "topic": "Test Subject",
        "subtopics": ["Unit Test"]
    }

    # 2. Launch Browser (Persistent, Visible)
    user_data_dir = os.path.abspath(os.path.join("outputs", "browser_data"))
    os.makedirs(user_data_dir, exist_ok=True)
    
    logger.info(f"Launching browser with user data: {user_data_dir}")
    
    async with async_playwright() as p:
        # Launch persistent context to keep login state
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False, # Visible!
            channel="chrome", # Use installed Chrome
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"]  # Hide "Chrome is being controlled..."
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        try:
            # 3. Run the Function
            logger.info("Calling run_notebooklm...")
            result = await run_notebooklm(chunks, context, page)
            logger.info("Test Complete! Result:")
            logger.info(result)
            
        except Exception as e:
            logger.error(f"Test Failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Keep browser open for inspection if failed
            logger.info("Keeping browser open for 30s for inspection...")
            await asyncio.sleep(30)
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_interactive_test())
