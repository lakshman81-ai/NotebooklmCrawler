import sys
import asyncio
from playwright.async_api import async_playwright

async def render(html_path, pdf_path):
    async with async_playwright() as p:
        # Launch strictly headless
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            # File URL needs correct formatting
            if not html_path.startswith("file:///"):
                # Handle Windows paths heavily
                # Simplest is to just pass what we got and hope playwright handles it or use absolute
                url = f"file:///{html_path}"
            else:
                url = html_path
                
            await page.goto(url)
            await page.pdf(path=pdf_path, format="A4", print_background=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pdf_gen.py <html_path> <pdf_path>")
        sys.exit(1)
    
    html = sys.argv[1]
    pdf = sys.argv[2]
    
    try:
        asyncio.run(render(html, pdf))
        print("SUCCESS")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
