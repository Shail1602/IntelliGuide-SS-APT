import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Path to your URLs file
FLEET_URLS_FILE = "scraper/fleets_urls.txt"
PDF_OUTPUT_DIR = "Fleet_pdfs"

# Ensure output folder exists
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

async def save_fleet_pages_as_pdf():
    # Read all fleet URLs
    with open(FLEET_URLS_FILE, "r") as f:
        fleet_urls = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in fleet_urls:
            ship_id = url.strip().split("/")[-1]
            print(f"📄 Saving PDF for: {ship_id}")

            try:
                await page.goto(url, timeout=60000)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(5000)  # Let content load

                pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{ship_id}.pdf")
                await page.pdf(path=pdf_path, format="A4")

                print(f"✅ Saved: {pdf_path}")
            except Exception as e:
                print(f"❌ Failed for {url}: {e}")

        await browser.close()

# Run the script
asyncio.run(save_fleet_pages_as_pdf())
