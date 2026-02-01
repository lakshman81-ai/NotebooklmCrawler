from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Navigating to app...")
        try:
            page.goto("http://localhost:8501", timeout=10000)
            page.wait_for_load_state("networkidle")

            # Streamlit loading
            time.sleep(5)

            print("Taking Dashboard screenshot...")
            page.screenshot(path="verification/ui_dashboard.png")

            # Click Settings Tab
            print("Clicking Settings tab...")
            # Using text locator for the tab
            page.get_by_text("⚙️ Settings").click()
            time.sleep(2)

            print("Taking Settings screenshot...")
            page.screenshot(path="verification/ui_settings.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")

        browser.close()

if __name__ == "__main__":
    run()
