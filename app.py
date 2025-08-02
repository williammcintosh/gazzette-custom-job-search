import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://gazette.education.govt.nz"
START_URL = f"{BASE_URL}/vacancies/?Regions=new-zealand-nation-wide&SectorsAndRoles=secondary-wharekura&LearningAreasStrand=the-new-zealand-curriculum&PositionTypes=full-time&sort=closing"

keywords = ["math", "digital"]
seen_links = set()

def scrape_page(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    vacancies = soup.select("article.block-vacancy-featured")
    for v in vacancies:
        title = v.select_one("h3.title").get_text(strip=True)
        description = v.select_one("p.description").get_text(separator=" ", strip=True).lower()
        href = v.select_one("a.search-statable")["href"]
        link = f"{BASE_URL}{href}"

        if link not in seen_links and any(word in description or word in title.lower() for word in keywords):
            seen_links.add(link)
            print(f"{title}\n{link}\n")

    # Find the next page link
    next_button = soup.select_one("a.next")
    if next_button and "href" in next_button.attrs:
        next_href = next_button["href"]
        return f"{BASE_URL}{next_href}"
    return None

# Loop through pages
next_url = START_URL
while next_url:
    next_url = scrape_page(next_url)
    time.sleep(1)  # be nice, don’t hammer their servers
