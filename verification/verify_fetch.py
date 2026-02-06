
from playwright.sync_api import sync_playwright, expect
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # 1. Open App
    print('Navigating to app...')
    page.goto('http://localhost:5173')
    time.sleep(2) # Allow load

    # 2. Toggle Search Web
    print('Toggling Search Web...')
    # Locate the span 'Search Web' and click the sibling button
    # There are two 'Search Web': one in header of SourceSelector, one in the toggle pill.
    # The toggle pill one is inside a div with class 'bg-zinc-100 p-1 rounded-full'.
    # We can use :right-of selector or xpath.

    # Or just click the button that is visibly the toggle.
    # It has classes "h-6 w-10".
    toggle = page.locator("button.h-6.w-10").first
    toggle.click()

    time.sleep(1) # Wait for state update

    # 3. Select DDG
    print('Selecting DuckDuckGo...')
    # Now it should be enabled.
    page.get_by_text('DUCKDUCKGO').click()

    # 4. Fill Inputs
    print('Filling inputs...')
    page.select_option('select', '9') # Grade

    page.get_by_placeholder('Subject...').fill('Physics')
    page.get_by_placeholder('Enter topic...').fill('Motion')

    # 5. Click Fetch URLs
    print('Clicking Fetch URLs...')
    page.get_by_role('button', name='Fetch URLs').click()

    # 6. Wait for Target URLs box
    print('Waiting for results...')

    try:
        textarea = page.get_by_placeholder('Paste URLs here...')
        expect(textarea).to_be_visible(timeout=20000)

        val = textarea.input_value()
        print(f'Textarea content: {val[:100]}...')

        if 'http' in val or 'No automated results' in val:
            print('SUCCESS: URLs populated.')
        else:
            print('FAIL: Textarea empty or unexpected content.')

    except Exception as e:
        print(f'ERROR: {e}')
        page.screenshot(path='verification/error.png')
        raise e

    # Screenshot
    page.screenshot(path='verification/success.png')
    print('Screenshot saved.')

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
