from playwright.sync_api import sync_playwright
import time
import json

def handle_execute(route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"success": True, "message": "Pipeline started"})
    )

def handle_logs_running(route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "status": "RUNNING",
            "logs": [
                {"level": "INFO", "component": "SYSTEM", "message": "Initiating mission protocol..."},
                {"level": "INFO", "component": "CONFIG", "message": "Source: GOOGLE | Web Search: ON"},
                {"level": "INFO", "component": "NotebookLM Driver", "message": "Initializing NotebookLM driver..."},
                {"level": "INFO", "component": "Source Discovery", "message": "Searching Google for 'Quantum Physics' grade 9..."},
                {"level": "INFO", "component": "Source Discovery", "message": "Found 5 high-quality sources."},
                {"level": "INFO", "component": "Inference Engine", "message": "Processing content for 'Connect' difficulty..."}
            ]
        })
    )

def handle_logs_completed(route):
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({
            "status": "COMPLETED",
            "logs": [
                {"level": "INFO", "component": "SYSTEM", "message": "Mission Complete"},
                {"level": "INFO", "component": "Artifact Serialization", "message": "Saved 3 artifacts to outputs/final"}
            ]
        })
    )

def run_mock():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # PC Browser Optimization: 1920x1080
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # 1. Screen 1: Input Setup
        page.goto("http://localhost:5173")
        time.sleep(2) # Wait for hydration

        # Fill Data

        # Search Web Toggle (Enable) - MUST DO FIRST to enable Topic input
        # The toggle is next to "Search Web" text.
        # Use a more specific locator to avoid matching parent containers
        page.locator(".bg-slate-800").filter(has_text="Search Web").locator("button").click()

        # Topic
        page.fill("input[placeholder='Enter main topic...']", "Quantum Physics")

        # Select Grade 9
        page.select_option("select", "9")

        # Select Subject Physics
        page.fill("input[list='subjects-list']", "Physics")

        # Select Google (should be enabled now)
        page.click("button:has-text('GOOGLE')")

        # Select Difficulty 'Extend'
        page.click("div:has-text('Extend')")

        time.sleep(1) # Visual settle
        page.screenshot(path="verification/mock_run_1_input.png")
        print("Screen 1: Input captured.")

        # 2. Screen 2: Running
        # Setup API Interception
        page.route("**/api/auto/execute", handle_execute)
        page.route("**/api/logs", handle_logs_running)

        # Click Launch
        page.click("button:has-text('LAUNCH RESEARCH PIPELINE')")

        time.sleep(3) # Wait for progress bar to animate and logs to appear
        page.screenshot(path="verification/mock_run_2_running.png")
        print("Screen 2: Running captured.")

        # 3. Screen 3: Output
        # Update logs to completed
        page.unroute("**/api/logs")
        page.route("**/api/logs", handle_logs_completed)

        time.sleep(3) # Wait for polling to pick up COMPLETED status

        # Switch to Output Tab
        page.click("button:has-text('OUTPUT (Synthesis)')")

        time.sleep(1)
        page.screenshot(path="verification/mock_run_3_output.png")
        print("Screen 3: Output captured.")

        browser.close()

if __name__ == "__main__":
    run_mock()
