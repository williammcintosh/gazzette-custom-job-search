import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import time

BASE_URL = "https://gazette.education.govt.nz"

# ---------- prompts + helpers ----------
def prompt_yes_no(msg, default=False):
    hint = "Y/n" if default else "y/N"
    ans = input(f"{msg} ({hint}) ").strip().lower()
    if not ans:
        return default
    return ans.startswith("y")

def normalize_keywords(raw: str, default):
    tokens = [t.strip().lower() for t in raw.split(",")]
    tokens = [t for t in tokens if re.search(r"[a-z]", t)]
    tokens = [t for t in tokens if len(t) > 1 or t in {"x"}]
    seen, cleaned = set(), []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            cleaned.append(t)
    return cleaned or default[:]

DEFAULT_KEYWORDS = ["math", "digital"]

def collect_filters():
    while True:
        new_teacher_only = prompt_yes_no("New Teachers only", default=False)
        perm_only = prompt_yes_no("Permanent positions only", default=False)
        raw = input(f"Key words (comma separated) [default: {', '.join(DEFAULT_KEYWORDS)}]: ").strip()
        keywords = normalize_keywords(raw if raw else "", DEFAULT_KEYWORDS)

        print("\nConfirm your choices:")
        print(f"  New Teacher only: {new_teacher_only}")
        print(f"  Permanent only:   {perm_only}")
        print(f"  Keywords:         {keywords}")
        if prompt_yes_no("Proceed", default=True):
            return new_teacher_only, perm_only, keywords
        print("Ok, let's try again.\n")

new_teacher_only, perm_only, keywords = collect_filters()

START_URL = (
    f"{BASE_URL}/vacancies/?Regions=new-zealand-nation-wide&"
    f"SectorsAndRoles=secondary-wharekura&LearningAreasStrand=the-new-zealand-curriculum&"
    f"PositionTypes=full-time&IsBeginningTeachers={'1' if new_teacher_only else '0'}&sort=closing"
)

print("\nFilters:")
print(f"  New Teacher only: {new_teacher_only}")
print(f"  Permanent only:   {perm_only}")
print(f"  Keywords:         {keywords}\n")

seen_links = set()

# ---------- utils ----------
def progress_bar(current, total, width=30):
    ratio = 0 if total == 0 else min(max(current / total, 0), 1)
    filled = int(width * ratio)
    bar = "█" * filled + "-" * (width - filled)
    sys.stdout.write(f"\r[{bar}] {current}/{total} pages loaded...")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n\n")

def parse_date_str(s):
    if not s or "unknown" in s.lower():
        return None
    s = s.replace(",", " ").strip()
    try:
        return datetime.strptime(s, "%d %b %Y")
    except:
        try:
            return datetime.strptime(s, "%d %B %Y")
        except:
            return None

def read_calendar_date(container):
    if not container:
        return "Unknown"
    txt = container.get_text(" ", strip=True)
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b", txt)
    if m:
        return f"{m.group(1)} {m.group(2)} {m.group(3)}"
    day = container.select_one("span.day")
    month = container.select_one("span.month")
    year = container.select_one("span.year")
    if day and year:
        mtxt = month.get_text(strip=True) if month else ""
        return f"{day.get_text(strip=True)} {mtxt} {year.get_text(strip=True)}".strip()
    return "Unknown"

def get_total_pages(soup):
    max_page = 1
    for a in soup.select("nav.nav-pagination ol li a[title*='View page number']"):
        t = a.get("title", "")
        m = re.search(r"page number\s+(\d+)", t)
        if m:
            max_page = max(max_page, int(m.group(1)))
    return max_page

# ---------- scrape pieces ----------
def check_job_details(job_url):
    resp = requests.get(job_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # employment type (Permanent vs Fixed term etc)
    emp_tag = soup.select_one("p.title-byline[itemprop='employmentType'], p.title-byline")
    emp_text = emp_tag.get_text(" ", strip=True) if emp_tag else "Unknown"

    if perm_only and "permanent" not in emp_text.lower():
        return None

    # new teacher suitability
    bt_tag = soup.find("div", class_="tip")
    is_beginning = False
    if bt_tag and "suitable for beginning teachers" in bt_tag.get_text(strip=True).lower():
        is_beginning = True
    if new_teacher_only and not is_beginning:
        return None

    school_name_tag = soup.select_one("div.layout-col-7 h3[itemprop='name']")
    school_name = school_name_tag.get_text(strip=True) if school_name_tag else "Unknown School"

    def extract_field(label):
        tag = soup.find("strong", string=label)
        if tag and tag.next_sibling:
            return str(tag.next_sibling).strip().replace("<br>", "").replace("\n", "")
        return "Unknown"

    authority = extract_field("Authority:")
    gender = extract_field("Gender:")

    address_tag = soup.select_one("p[itemprop='address'] span[itemprop='streetAddress']")
    address = address_tag.get_text(strip=True) if address_tag else "Unknown"

    map_tag = soup.select_one("p.link-map a[href*='maps.google.com']")
    map_url = map_tag["href"] if map_tag else None

    listed_date = read_calendar_date(soup.select_one("div.cal-icon.start"))
    close_date  = read_calendar_date(soup.select_one("div.cal-icon.end"))

    return authority, school_name, gender, address, map_url, listed_date, close_date, emp_text, is_beginning


def scrape_page(url, results):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    vacancies = soup.select("article.block-vacancy-featured")
    for v in vacancies:
        title_el = v.select_one("h3.title")
        desc_el = v.select_one("p.description")
        link_el = v.select_one("a.search-statable")
        if not title_el or not desc_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        description = desc_el.get_text(separator=" ", strip=True).lower()
        href = link_el["href"]
        link = f"{BASE_URL}{href}"

        if any(skip_word in title.lower() for skip_word in ["principal", "deputy"]):
            continue

        if not any(word in description or word in title.lower() for word in keywords):
            continue

        if link in seen_links:
            continue

        details = check_job_details(link)
        if not details:
            continue

        authority, school_name, gender, address, map_url, listed_date, close_date, emp_text, is_beginning = details
        seen_links.add(link)

        results[link] = {
            "title": title,
            "school": school_name,
            "gender": gender,
            "location": address,
            "authority": authority,
            "listed": listed_date,
            "closes": close_date,
            "closes_dt": parse_date_str(close_date),
            "employment": emp_text,
            "beginning_teacher": "Yes" if is_beginning else "No",
            "map": map_url,
            "url": link,
        }


    next_button = soup.select_one("a.next")
    next_url = f"{BASE_URL}{next_button['href']}" if next_button and next_button.has_attr("href") else None
    return next_url, soup

# ---------- run ----------
results = {}
next_url = START_URL

resp0 = requests.get(next_url)
resp0.raise_for_status()
soup0 = BeautifulSoup(resp0.text, "html.parser")
total_pages = get_total_pages(soup0)

current_page = 0
while next_url:
    current_page += 1
    progress_bar(current_page, total_pages)
    next_url, soup = scrape_page(next_url, results)
    time.sleep(1)

sorted_jobs = sorted(results.values(), key=lambda x: (x["closes_dt"] is None, x["closes_dt"]))

for i, job in enumerate(sorted_jobs, 1):
    print(f"{i}. {job['title']}")
    print(f"  • {job['school']}")
    print(f"  • Gender: {job['gender']}")
    print(f"  • Employment: {job['employment']}")
    print(f"  • Beginning Teacher: {job['beginning_teacher']}")
    print(f"  • Location: {job['location']}")
    print(f"  • Authority: {job['authority']}")
    print(f"  • Listed: {job['listed']}")
    print(f"  • Closes: {job['closes']}")
    print(f"  • {job['url']}")
    if job['map']:
        print(f"  • {job['map']}")
    print()
