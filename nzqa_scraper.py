import csv
SCHOOLS = {377, 203, 495}
CSV_PATH = "Participation-Qualification-Attainment-Statistics-National-2024-20250302.csv"  # put the real filename here

latest = {}  # school_code -> (year, percent)

with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        try:
            qual = row.get("Qualification") or row.get("qualification")
            school = int(row.get("School Code") or row.get("Provider Code") or row.get("school_code"))
            year = int(row.get("Year") or row.get("year"))
            pct = row.get("% of roll") or row.get("Percent of roll") or row.get("percent")
        except Exception:
            continue
        if qual != "University Entrance" or school not in SCHOOLS:
            continue
        # normalize percent text like "34.5" or "34.5%"
        if pct is None or pct == "":
            continue
        pct_num = float(str(pct).replace("%","").strip())
        if school not in latest or year > latest[school][0]:
            latest[school] = (year, pct_num)

for school in SCHOOLS:
    if school in latest:
        y, p = latest[school]
        print(f"School {school}: UE {p}% in {y}")
    else:
        print(f"School {school}: no UE data in file")
