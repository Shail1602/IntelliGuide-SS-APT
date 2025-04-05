import asyncio
import json
from playwright.async_api import async_playwright

TOUR_LIST_FILE = "scraper/tour_urls.txt"
OUTPUT_FILE = "scraper/tour_info.json"

async def extract_tour_info(tour_url, page):
    result = {}

    try:
        await page.goto(tour_url, timeout=60000)
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)

        result["original_url"] = tour_url

        # Trip Name
        try:
            trip_name = await page.locator("h1").first.text_content()
            result["trip_name"] = trip_name.strip() if trip_name else ""
        except:
            result["trip_name"] = ""

        # Trip Code
        try:
            trip_code = await page.locator("text=/Trip code/i").first.text_content()
            trip_code = trip_code.replace("Trip code", "").replace(":", "").strip()
            result["trip_code"] = trip_code
        except:
            result["trip_code"] = ""

        # Region and Country from URL
        parts = tour_url.split("/tours/")[-1].split("/")
        result["region"] = parts[0].capitalize() if len(parts) > 0 else ""
        result["country"] = parts[1].capitalize() if len(parts) > 1 else ""

        # Hero Description
        try:
            desc_locator = page.locator("div.hero-tour__summary p, div.hero__content p")
            desc = await desc_locator.first.text_content()
            result["description"] = desc.strip() if desc else ""
        except:
            result["description"] = ""

        # Trip Inclusions
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            inclusion_spans = page.locator("section >> div.d_grid span:not([class*='d_none'])")
            count = await inclusion_spans.count()
            inclusions = []

            for i in range(count):
                text = await inclusion_spans.nth(i).text_content()
                if text and text.strip():
                    inclusions.append(text.strip())

            result["trip_inclusions"] = inclusions
        except:
            result["trip_inclusions"] = []

        # Booking URL
        try:
            booking_url = await page.locator('a[href*="booking.aptouring.com"]').first.get_attribute("href")
            result["booking_url"] = booking_url
        except:
            result["booking_url"] = ""

        # Booking Page Info
        if result["booking_url"]:
            try:
                await page.goto(result["booking_url"], timeout=60000)
                await page.wait_for_timeout(3000)
                await page.wait_for_selector(".chakra-card__body", timeout=10000)
                card = page.locator(".chakra-card__body").first

                dates = await card.locator("p.chakra-text.css-1r6zo4l").all_text_contents()
                result["start_date"] = dates[0].strip() if len(dates) > 0 else ""
                result["end_date"] = dates[1].strip() if len(dates) > 1 else ""

                price = await card.locator("p.chakra-text.css-68j6fv").first.text_content()
                result["price_aud"] = price.strip() if price else ""

                is_limited = await page.locator("text='Limited availability'").count() > 0
                result["limited_availability"] = is_limited
            except:
                result["start_date"] = ""
                result["end_date"] = ""
                result["price_aud"] = ""
                result["limited_availability"] = False

    except Exception as e:
        print(f"⚠️ Error processing {tour_url}: {e}")
    
    return result

async def main():
    all_results = []

    with open(TOUR_LIST_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for i, url in enumerate(urls):
            print(f"🔍 [{i+1}/{len(urls)}] Processing: {url}")
            data = await extract_tour_info(url, page)
            all_results.append(data)

        await browser.close()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✅ Saved all results to: {OUTPUT_FILE}")

# Run it
asyncio.run(main())
