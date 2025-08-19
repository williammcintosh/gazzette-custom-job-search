import re, time, sys
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "en-NZ,en;q=0.9"
}

def get_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text

def get_school_name_from_gazette(vacancy_url):
    html = get_html(vacancy_url)
    soup = BeautifulSoup(html, "html.parser")
    # common selector on Gazette vacancy pages
    name = None
    tag = soup.select_one("div.layout-col-7 h3[itemprop='name']")
    if tag:
        name = tag.get_text(strip=True)
    if not name:
        # fallback to the first strong or h3 near Employer label
        for lbl in soup.find_all(text=re.compile(r"Employer|School", re.I)):
            parent = getattr(lbl, "parent", None)
            if parent:
                nxt = parent.find_next(["strong","h3"])
                if nxt:
                    name = nxt.get_text(strip=True)
                    break
    if not name:
        raise RuntimeError("Could not find school name on Gazette page")
    return name

def find_education_counts_profile(school_name):
    # Use Education Counts on-site search, then pick profile link
    q = quote_plus(school_name)
    search_url = f"https://www.educationcounts.govt.nz/search?q={q}&sa=Search"
    html = get_html(search_url)
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/find-school/school/profile?school=" in href:
            # ensure absolute
            if href.startswith("/"):
                href = "https://www.educationcounts.govt.nz" + href
            return href
    raise RuntimeError("Education Counts profile not found in search results")

def find_school_qualifications_url(profile_url):
    html = get_html(profile_url)
    soup = BeautifulSoup(html, "html.parser")
    # Look for link text containing School Qualifications
    link = None
    for a in soup.find_all("a", href=True):
        if re.search(r"School\s+Qualifications", a.get_text(strip=True), re.I):
            link = a["href"]
            break
    if not link:
        # sometimes the tab link is in nav lists
        for a in soup.select("a[href]"):
            if "qualifications" in a.get_text(strip=True).lower():
                link = a["href"]; break
    if not link:
        raise RuntimeError("School Qualifications link not found on profile")
    if link.startswith("/"):
        link = "https://www.educationcounts.govt.nz" + link
    else:
        link = urljoin(profile_url, link)
    return link

def extract_latest_ue_percent(qual_url):
    html = get_html(qual_url)
    soup = BeautifulSoup(html, "html.parser")

    # Find the table associated with University Entrance
    ue_table = None

    # Strategy 1. header or caption mentions University Entrance
    for tbl in soup.find_all("table"):
        caption = tbl.find("caption")
        if caption and re.search(r"University\s+Entrance", caption.get_text(" ", strip=True), re.I):
            ue_table = tbl; break
        # check preceding header
        prev = tbl.find_previous(["h2","h3","h4"])
        if prev and re.search(r"University\s+Entrance", prev.get_text(" ", strip=True), re.I):
            ue_table = tbl; break

    if not ue_table:
        # Strategy 2. any text node UE then next table
        hit = soup.find(string=re.compile(r"University\s+Entrance", re.I))
        if hit:
            nxt_tbl = BeautifulSoup(str(hit), "html.parser")
        # fallback sweep
        for tbl in soup.find_all("table"):
            ths = [th.get_text(" ", strip=True) for th in tbl.find_all("th")]
            if any(re.search(r"University\s*Entrance", t, re.I) for t in ths):
                ue_table = tbl; break

    if not ue_table:
        raise RuntimeError("UE table not found")

    # Parse header years and locate percent column by year
    # Many EC tables have first column Year, and columns like Count, Percentage
    # Build rows
    rows = []
    for tr in ue_table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th","td"])]
        if cells:
            rows.append(cells)

    if len(rows) < 2:
        raise RuntimeError("UE table empty")

    # Find indexes
    header = [h.lower() for h in rows[0]]
    # pick year column
    try:
        year_idx = header.index("year")
    except ValueError:
        # fallback find a column that looks like a year
        year_idx = None
        for i, h in enumerate(header):
            if re.search(r"year", h):
                year_idx = i; break
        if year_idx is None:
            # try to detect by values in column 0
            year_idx = 0

    # find percent column
    pct_idx = None
    for i,h in enumerate(header):
        if re.search(r"%|percent", h):
            pct_idx = i; break
    if pct_idx is None and len(header) >= 3:
        # guess last col
        pct_idx = len(header) - 1

    # collect year -> percent
    data = []
    for r in rows[1:]:
        if year_idx >= len(r) or pct_idx >= len(r): 
            continue
        ytxt = r[year_idx]
        m = re.search(r"(20\d{2})", ytxt)
        if not m:
            continue
        year = int(m.group(1))
        pct_txt = r[pct_idx]
        m2 = re.search(r"(\d+(?:\.\d+)?)", pct_txt.replace(",", ""))
        if not m2:
            continue
        pct = float(m2.group(1))
        data.append((year, pct))

    if not data:
        raise RuntimeError("Could not parse UE percent data")

    latest_year, latest_pct = max(data, key=lambda t: t[0])
    return latest_year, latest_pct

def get_latest_ue_for_vacancy(vacancy_url):
    school = get_school_name_from_gazette(vacancy_url)
    profile = find_education_counts_profile(school)
    qual = find_school_qualifications_url(profile)
    year, pct = extract_latest_ue_percent(qual)
    return {"school": school, "profile": profile, "qualifications_page": qual, "year": year, "ue_percent": pct}

if __name__ == "__main__":
    vacancies = [
        "https://gazette.education.govt.nz/vacancies/1HAoXQ-mathematics-teacher/",
        "https://gazette.education.govt.nz/vacancies/1HAoXJ-mathematics-teacher/",
        "https://gazette.education.govt.nz/vacancies/1HAoTC-teacher-of-mathematics-with-statistics/"
    ]
    for url in vacancies:
        try:
            res = get_latest_ue_for_vacancy(url)
            print(f"{res['school']}: UE {res['ue_percent']}% in {res['year']}")
            print(f"Profile {res['profile']}")
            print(f"Quals  {res['qualifications_page']}")
        except Exception as e:
            print(f"Failed for {url}: {e}", file=sys.stderr)
        time.sleep(1.5)
