"""
Custom parser for Birmingham City University clearing page.
Activate by setting  scrape_method: "custom"  in config.py for the BCU entry.

Update the selectors below once you inspect BCU's live clearing page.
"""

from bs4 import BeautifulSoup


def extract(soup: BeautifulSoup) -> list[dict]:
    results = []

    # --- Update these selectors after inspecting the live BCU clearing page ---
    # Example: BCU uses a <table class="clearing-vacancies"> structure
    table = soup.find("table", class_=lambda c: c and "clearing" in c.lower())
    if not table:
        # Try any table
        table = soup.find("table")
    if not table:
        return results

    rows = table.find_all("tr")
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        course  = cells[0].get_text(strip=True)
        req     = cells[-1].get_text(strip=True)  # assume last col = entry req
        if course:
            results.append({"course": course, "entry_req": req or "N/A"})

    return results
