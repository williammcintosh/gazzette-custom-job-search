# Education Gazette Job Scraper

This is a Python script that scrapes secondary school teaching vacancies from the [New Zealand Education Gazette](https://gazette.education.govt.nz) website. It looks for jobs that match certain keywords (like "math" or "digital") and collects details such as school name, authority, address, gender, map link, date listed, and closing date. Results are automatically sorted by the soonest closing date.

## Features

- Filters vacancies by keywords in the title or description
- Skips leadership roles (Principal, Deputy)
- Skips non-permanent jobs
- Collects:
  - Job title
  - School name
  - Authority (State, State-integrated, Private)
  - Gender (Co-ed, Girls, Boys)
  - Location (street address)
  - Map link (Google Maps)
  - Date listed
  - Closing date
  - Vacancy link
- Supports pagination and shows a progress bar
- Automatically sorts results by soonest closing date (unknown dates go last)

## Requirements

- Python 3.8 or newer
- [requests](https://pypi.org/project/requests/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

Install dependencies with:

```bash
pip install requests beautifulsoup4
```

## Usage

Run the script directly:

```bash
python app.py
```

The script will:

1. Start from the "Secondary Wharekura" vacancies page.
2. Detect total pages and show a progress bar as it crawls through.
3. Skip non-permanent and leadership roles.
4. Collect and print job details.
5. Display results sorted by closing date.

## Customization

- Edit the `keywords` list in `app.py` to target specific subjects (e.g., `["math", "science", "digital"]`).
- Adjust filters in `scrape_page` if you want to include leadership or fixed-term positions.

## Notes

- The script waits 1 second between page requests to be polite to the server.
- Dates are parsed into proper `datetime` objects for accurate sorting.
- Progress bar shows how many pages have been scraped.

## Example

```bash
27. Maths teacher
  • Green Bay High School
  • Gender: Co-Ed
  • Location: 143-161 Godley Road, Green Bay, Auckland
  • Authority: State
  • Listed: 19 August 2025
  • Closes: 01 September 2025
  • https://gazette.education.govt.nz/vacancies/1HAobX-maths-teacher-2/
  • http://maps.google.com/maps?z=12&t=m&q=loc:-36.93095+174.669395
```
