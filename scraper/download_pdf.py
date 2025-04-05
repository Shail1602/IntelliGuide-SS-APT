
import asyncio
import os
from playwright.async_api import async_playwright

async def download_pdf_with_playwright(url, folder="pdfs"):
    os.makedirs(folder, exist_ok=True)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, timeout=60000)

            async with page.expect_download() as download_info:
                await page.click('a:has-text("Save PDF")')
            download = await download_info.value

            filename = download.suggested_filename
            path = os.path.join(folder, filename)
            await download.save_as(path)

            print(f"✅ Downloaded: {filename}")
            await browser.close()
    except Exception as e:
        print(f"❌ Failed to download from {url}: {e}")

async def run():
    file_path = "scraper/tour_urls.txt"
    if not os.path.exists(file_path):
        print("❌ tour_urls.txt not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]

    for url in urls:
        print(f"🔍 Visiting: {url}")
        await download_pdf_with_playwright(url)

if __name__ == "__main__":
    asyncio.run(run())
