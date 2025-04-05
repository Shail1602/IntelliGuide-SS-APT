import requests
from bs4 import BeautifulSoup

# URL of the sitemap
sitemap_url = 'https://www.aptouring.com/en-au/sitemap.xml'

# Fetch the sitemap content
response = requests.get(sitemap_url)
sitemap_content = response.text

# Parse the XML
soup = BeautifulSoup(sitemap_content, 'xml')

# Find all <loc> tags
urls = [loc.text for loc in soup.find_all('loc')]

# Filter for tour detail pages
tour_detail_pages = [url for url in urls if '/tours/' in url and url.count('/') > 6]

# Save to a file or use as needed
with open('scraper/tour_urls.txt', 'w') as f:
    for url in tour_detail_pages:
        f.write(url + '\n')

print(f"Extracted {len(tour_detail_pages)} tour detail pages.")
