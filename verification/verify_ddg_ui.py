from playwright.sync_api import sync_playwright, expect
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate to app
    print("Navigating to app...")
    page.goto("http://localhost:3000")

    # Wait for app to load
    page.wait_for_selector("text=Intelligence Source", timeout=10000)

    # Enable "Search Web"
    print("Enabling Search Web...")
    page.locator("button").filter(has=page.locator("div.bg-white.rounded-full")).first.click()

    # Wait for Search Web to be active
    expect(page.get_by_text("Trusted Sites")).to_be_visible()

    # Select DuckDuckGo
    print("Selecting DuckDuckGo...")
    page.get_by_role("button", name="DUCKDUCKGO").click()

    # Verify "Fetch URLs" button appears
    print("Verifying Fetch URLs button...")
    fetch_btn = page.get_by_role("button", name="Fetch URLs")
    expect(fetch_btn).to_be_visible()

    # Take screenshot
    print("Taking screenshot...")
    page.screenshot(path="verification/verify_ddg_ui_fixed.png", full_page=False)

    browser.close()
    print("Verification complete.")

with sync_playwright() as playwright:
    run(playwright)
