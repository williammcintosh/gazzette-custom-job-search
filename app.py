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

    school_name_tag = soup.select_one("div.layout-col-7 h3[itemprop='name']")
    school_name = school_name_tag.get_text(strip=True) if school_name_tag else "Unknown School"

    def extract_field(label):
        tag = soup.find("strong", string=label)
        if tag and tag.next_sibling:
            return tag.next_sibling.strip().replace("<br>", "").replace("\n", "")
        return "Unknown"

    authority = extract_field("Authority:")
    gender = extract_field("Gender:")

    address_tag = soup.select_one("p[itemprop='address'] span[itemprop='streetAddress']")
    address = address_tag.get_text(strip=True) if address_tag else "Unknown"

    map_tag = soup.select_one("p.link-map a[href*='maps.google.com']")
    map_url = map_tag["href"] if map_tag else None

    # Listed date
    listed_tag = soup.select_one("div.cal-icon.start")
    listed_date = "Unknown"
    if listed_tag:
        day = listed_tag.select_one("span.day")
        year = listed_tag.select_one("span.year")
        if day and year:
            listed_date = f"{day.get_text(strip=True)} {year.get_text(strip=True)}"

    # Closing date
    close_tag = soup.select_one("div.cal-icon.end")
    close_date = "Unknown"
    if close_tag:
        day = close_tag.select_one("span.day")
        year = close_tag.select_one("span.year")
        if day and year:
            close_date = f"{day.get_text(strip=True)} {year.get_text(strip=True)}"

    return authority, school_name, gender, address, map_url, listed_date, close_date


def scrape_page(url, counter):
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
                authority, school_name, gender, address, map_url, listed_date, close_date = check_job_details(link)
                seen_links.add(link)
                print(f"{counter}. {title}")
                print(f"  • {school_name}")
                print(f"  • Gender: {gender}")
                print(f"  • Location: {address}")
                print(f"  • Authority: {authority}")
                print(f"  • Listed: {listed_date}")
                print(f"  • Closes: {close_date}")
                print(f"  • {link}")
                if map_url:
                    print(f"  • {map_url}")
                print()
                counter+=1

    # Pagination
    next_button = soup.select_one("a.next")
    if next_button and "href" in next_button.attrs:
        next_href = next_button["href"]
        return f"{BASE_URL}{next_href}", counter
    return None, counter


# Start scraping
next_url = START_URL
count = 1
while next_url:
    next_url, count = scrape_page(next_url, count)
    time.sleep(1)