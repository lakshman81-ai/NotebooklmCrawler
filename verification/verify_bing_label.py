import sys
from playwright.sync_api import sync_playwright

def verify_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to local frontend
        # Assuming Vite dev server runs on 5173
        try:
            page.goto("http://localhost:5173", timeout=10000)
            page.wait_for_selector("text=BING", timeout=10000)

            # Take screenshot of the Intelligence Source area
            page.screenshot(path="verification/bing_ui_verify.png", full_page=True)
            print("Screenshot saved to verification/bing_ui_verify.png")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    verify_ui()
