# scraper/scrape_trip_detail_pages.py

import asyncio
import csv
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

with open("scraper/tour_urls.txt") as f:
    tour_detail_pages = [line.strip() for line in f if line.strip()]

def infer_region_from_url(url):
    try:
        path_parts = urlparse(url).path.strip("/").split("/")
        return path_parts[3].capitalize() if len(path_parts) > 3 else "Unknown"
    except:
        return "Unknown"

async def extract_tour_info(page, url):
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(15000)

    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')

    try:
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""

        # Meta or first <p> as intro
        meta_desc = soup.find("meta", attrs={"name": "description"})
        intro = meta_desc["content"] if meta_desc else (soup.find("p").get_text(strip=True) if soup.find("p") else "")

        # Highlights
        highlights = ""
        highlights_header = soup.find("h2", string=lambda x: x and "highlight" in x.lower())
        if highlights_header:
            ul = highlights_header.find_next("ul")
            if ul:
                highlights = "; ".join(li.get_text(strip=True) for li in ul.find_all("li"))

        # Itinerary
        itinerary_items = []
        for tag in soup.find_all(["h3", "h4", "div"]):
            if tag.text.strip().lower().startswith("day "):
                itinerary_items.append(tag.get_text(strip=True))
        itinerary = " | ".join(itinerary_items)

        # PDF
        pdf_link = ""
        pdf_tag = soup.find("a", href=lambda x: x and x.endswith(".pdf"))
        if pdf_tag:
            href = pdf_tag.get("href")
            pdf_link = "https://www.aptouring.com" + href if href and not href.startswith("http") else href

        # Extra metadata
        region = infer_region_from_url(url)

        # Bullet lists
        bullet_lists = soup.find_all("ul")
        all_bullets = []
        for ul in bullet_lists:
            all_bullets.extend(li.get_text(strip=True) for li in ul.find_all("li"))
        additional_info = " | ".join(all_bullets)

        # Heading structure
        section_headings = [h.get_text(strip=True) for h in soup.find_all(["h2", "h3"])]

        return {
            "Title": title,
            "URL": url,
            "Intro": intro,
            "Region": region,
            "Itinerary": itinerary,
            "Highlights": highlights,
            "Additional_Info": additional_info,
            "Section_Headings": " | ".join(section_headings),
            "Brochure_PDF": pdf_link
        }

    except Exception as e:
        print(f"❌ Failed to parse {url}: {e}")
        return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        extracted_data = []
        for url in tour_detail_pages:
            print(f"🌍 Visiting {url}")
            data = await extract_tour_info(page, url)
            if data:
                extracted_data.append(data)

        await browser.close()

        # Save results
        with open("tours_scraped.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[
                "Title", "URL", "Intro", "Region", "Itinerary",
                "Highlights", "Additional_Info", "Section_Headings", "Brochure_PDF"
            ])
            writer.writeheader()
            writer.writerows(extracted_data)

        print(f"✅ Extracted {len(extracted_data)} enriched tours. Saved to tours_scraped.csv")

if __name__ == "__main__":
    asyncio.run(run())
