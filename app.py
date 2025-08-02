import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://gazette.education.govt.nz"
START_URL = f"{BASE_URL}/vacancies/?Regions=new-zealand-nation-wide&SectorsAndRoles=secondary-wharekura&LearningAreasStrand=the-new-zealand-curriculum&PositionTypes=full-time&IsBeginningTeachers=1&sort=closing"

keywords = ["math", "digital"]
seen_links = set()


def check_job_details(job_url):
    resp = requests.get(job_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # School name
    school_name_tag = soup.select_one("div.layout-col-7 h3[itemprop='name']")
    school_name = school_name_tag.get_text(strip=True) if school_name_tag else "Unknown School"

    # Use DOM searching instead of relying on full block structure
    def extract_field(label):
        tag = soup.find("strong", string=label)
        if tag and tag.next_sibling:
            return tag.next_sibling.strip().replace("<br>", "").replace("\n", "")
        return "Unknown"

    authority = extract_field("Authority:")
    gender = extract_field("Gender:")
    decile = extract_field("Decile:")

    # Skip private schools
    if "private" in authority.lower():
        return True, school_name, gender, decile, "Unknown", None

    # Address
    address_tag = soup.select_one("p[itemprop='address'] span[itemprop='streetAddress']")
    address = address_tag.get_text(strip=True) if address_tag else "Unknown"

    # Map link
    map_tag = soup.select_one("p.link-map a[href*='maps.google.com']")
    map_url = map_tag["href"] if map_tag else None

    return False, school_name, gender, decile, address, map_url




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

        # Skip leadership roles
        if any(skip_word in title.lower() for skip_word in ["principal", "deputy"]):
            continue

        # Only process if relevant keywords are present
        if any(word in description or word in title.lower() for word in keywords):
            if link not in seen_links:
                is_independent, school_name, gender, decile, address, map_url = check_job_details(link)
                if is_independent:
                    continue
                seen_links.add(link)
                print(f"{title}")
                print(f"  • {school_name}")
                print(f"  • Gender: {gender}")
                print(f"  • Decile: {decile}")
                print(f"  • Location: {address}")
                print(f"  • {link}")
                if map_url:
                    print(f"  • {map_url}")
                print()

    # Pagination
    next_button = soup.select_one("a.next")
    if next_button and "href" in next_button.attrs:
        next_href = next_button["href"]
        return f"{BASE_URL}{next_href}"
    return None

# Start scraping
next_url = START_URL
while next_url:
    next_url = scrape_page(next_url)
    time.sleep(1)
