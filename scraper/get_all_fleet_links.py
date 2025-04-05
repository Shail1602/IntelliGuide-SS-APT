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
fleet_detail_pages = [url for url in urls if '/our-fleet/' in url and url.count('/') > 4]

# Save to a file or use as needed
with open('scraper/fleets_urls.txt', 'w') as f:
    for url in fleet_detail_pages:
        f.write(url + '\n')


print(f"Extracted {len(fleet_detail_pages)} fleet detail pages.")

