from playwright.sync_api import sync_playwright
import time

def verify_changes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 2000}) # Larger viewport

        print("Navigating to home...")
        for i in range(10):
            try:
                page.goto("http://localhost:5173")
                break
            except:
                time.sleep(1)

        # ... (Checks for tabs same as before) ...
        print("Checking Tabs...")
        prompt_gen_tab = page.get_by_role("button", name="Prompt Generator")
        prompt_gen_tab.wait_for(state="visible", timeout=5000)

        # Navigate to Prompt Generator
        prompt_gen_tab.click()

        # Click Generate Report Prompts button to show the output section
        print("Generating report to reveal Jules Prompt...")
        generate_btn = page.get_by_role("button", name="Generate Report Prompts")
        generate_btn.click()

        # Wait for Jules Prompt section
        try:
            page.get_by_text("Jules Prompt (Editable)").wait_for(state="visible", timeout=5000)
            print("SUCCESS: Jules Prompt section found.")
        except:
             print("FAILURE: Jules Prompt section not found.")

        page.screenshot(path="verification_prompt_generator.png", full_page=True)
        print("Screenshot saved: verification_prompt_generator.png")

        # Config Tab verification
        page.get_by_role("button", name="Config").click()

        # Check for version text
        try:
            # It might be in the footer or bottom right
            version_el = page.get_by_text("ver.", exact=False)
            version_el.first.wait_for(state="visible", timeout=5000)
            print(f"SUCCESS: Version found: {version_el.first.text_content()}")
        except:
            print("FAILURE: Version text not found.")

        page.screenshot(path="verification_config.png", full_page=True)
        print("Screenshot saved: verification_config.png")

        browser.close()

if __name__ == "__main__":
    verify_changes()
