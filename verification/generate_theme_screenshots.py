import asyncio
import os
import time
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        # 1. Start Frontend (Assumes 'npm run preview' is running on 4173 or 'npm run dev' on 5173)
        # We will try 4173 first (preview port)
        url = "http://localhost:4173"
        try:
            await page.goto(url, timeout=5000)
        except:
            url = "http://localhost:5173"
            await page.goto(url)

        print(f"Connected to {url}")

        # Wait for app to load
        await page.wait_for_selector('text=Intelligence Source', timeout=10000)

        # --- SCREEN 1: INPUT ---
        print("Capturing Input State...")
        await page.screenshot(path="verification/theme_1_input.png")

        # --- PREPARE FOR RUNNING STATE ---
        # Fill inputs to pass validation
        # Toggle Web Search ON to make it easier (less fields required? No, more fields).
        # Let's keep Web Search OFF (default).
        # We need Target URLs or Local File.
        await page.fill('textarea[placeholder="Paste URLs here..."]', 'https://en.wikipedia.org/wiki/Artificial_intelligence')

        # Mock the backend execute call to hang so we stay in RUNNING state
        await page.route("**/api/auto/execute", lambda route: route.fulfill(
            status=200,
            body='{"success": true}',
            headers={"Content-Type": "application/json"}
        ))

        # Mock logs to show "RUNNING"
        # We need to return a running status initially
        await page.route("**/api/logs", lambda route: route.fulfill(
            status=200,
            body='{"logs": ["System initializing...", "Loading modules..."], "status": "RUNNING"}',
            headers={"Content-Type": "application/json"}
        ))

        # Click Launch
        print("Clicking Launch...")
        await page.click('button:has-text("INITIALIZE MISSION")')

        # Wait for Running Overlay
        await page.wait_for_selector('text=Mission In Progress', timeout=5000)

        # --- SCREEN 2: RUNNING ---
        print("Capturing Running State...")
        # Wait a bit for animations
        await asyncio.sleep(2)
        await page.screenshot(path="verification/theme_2_running.png")

        # --- SCREEN 3: OUTPUT ---
        print("Transitioning to Output...")

        # Update mock logs to return COMPLETED
        await page.unroute("**/api/logs")
        await page.route("**/api/logs", lambda route: route.fulfill(
            status=200,
            body='{"logs": ["Analysis complete.", "Generating artifacts...", "Mission Successful."], "status": "COMPLETED"}',
            headers={"Content-Type": "application/json"}
        ))

        # Wait for polling to pick up the change (interval is 2s)
        await asyncio.sleep(3)

        # It should auto-switch to Output tab and show success
        await page.wait_for_selector('text=Mission Successful', timeout=10000)

        # Wait for animations
        await asyncio.sleep(1)
        await page.screenshot(path="verification/theme_3_output.png")

        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(run())
