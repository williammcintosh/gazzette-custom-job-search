import requests
from bs4 import BeautifulSoup

def scrape_school(school_id):
    url = f"https://www.educationcounts.govt.nz/find-school/school?school={school_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/139.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for table in soup.find_all("table"):
        table_text = table.get_text(separator=" ", strip=True)
        if "NCEA" in table_text or "University Entrance" in table_text:
            print(f"\n=== NCEA / UE Table for School {school_id} ===")
            print(table_text)

        if "Destination" in table_text or "University" in table_text:
            print(f"\n=== Destinations Table for School {school_id} ===")
            print(table_text)

scrape_school(319)
