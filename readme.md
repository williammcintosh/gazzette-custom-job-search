# Education Gazette Job Scraper

This is a Python script that scrapes secondary school teaching vacancies from the [New Zealand Education Gazette](https://gazette.education.govt.nz) website. It looks for jobs that match certain keywords (like "math" or "digital") and collects details such as school name, authority, address, gender, map link, date listed, and closing date.

## Features

- Filters vacancies by keywords in the title or description
- Skips leadership roles (Principal, Deputy)
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
- Supports pagination to scrape all relevant vacancies

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
2. Crawl through all pages.
3. Print job details to the terminal.
4. Automatically looks for keywords "math" and "digital"

## Customization

- Edit the `keywords` list in `app.py` to target specific subjects (e.g., `["math", "science", "digital"]`).
- Adjust filters in `scrape_page` if you want to include leadership positions.

## Notes

- The script waits 1 second between page requests to be polite to the server.
- Dates are pulled in the format used on the Gazette site (e.g., `19 August 2025`).
- Sorting by closing date can be added easily using Python’s `datetime` module if you want to organize results.

## Example

```
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
