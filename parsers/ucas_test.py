"""
Custom parser for UCAS course search results page.
URL: https://www.ucas.com/explore/search/results?query=accounting+finance

This page has the same structure as a clearing page:
  - Course title (e.g. "Accounting and Finance")
  - University name
  - Entry requirements (UCAS points, e.g. "120" or grade profile "BBB")

We extract course+university as the identifier, and the tariff/grade as the
entry requirement — identical to what we'll do for real clearing pages.
"""

import re
from bs4 import BeautifulSoup


def extract(soup: BeautifulSoup) -> list[dict]:
    results = []

    # UCAS search results are rendered as cards / list items.
    # Each course card typically has:
    #   - A heading with the course title
    #   - A sub-heading with the university
    #   - A tariff / entry requirements section

    # Strategy A: look for article/li/div cards with course headings
    cards = (
        soup.find_all("article")
        or soup.find_all("li", class_=re.compile(r"(course|result|card)", re.I))
        or soup.find_all("div", class_=re.compile(r"(course-card|result-card|search-result)", re.I))
    )

    for card in cards:
        # Course title
        heading = card.find(re.compile(r"^h[1-5]$"))
        if not heading:
            heading = card.find(class_=re.compile(r"(title|course-name|heading)", re.I))
        if not heading:
            continue
        course_title = heading.get_text(strip=True)

        # University name (to make identifier unique)
        uni_el = card.find(class_=re.compile(r"(provider|university|institution|uni-name)", re.I))
        uni_name = uni_el.get_text(strip=True) if uni_el else ""

        # Entry requirement / tariff
        tariff_el = card.find(class_=re.compile(r"(tariff|points|entry|requirement|grade)", re.I))
        if tariff_el:
            tariff = tariff_el.get_text(strip=True)
        else:
            # Search for a numeric pattern that looks like UCAS points in card text
            card_text = card.get_text(separator=" ")
            m = re.search(r"\b(\d{2,3})\s*(?:UCAS\s*)?(?:points?|tariff|pts)\b", card_text, re.I)
            tariff = m.group(0) if m else "See course"

        identifier = f"{course_title}" + (f" – {uni_name}" if uni_name else "")
        if identifier:
            results.append({
                "course":    identifier[:80],
                "entry_req": tariff or "N/A",
            })

    # Strategy B: if no cards found, look for a <table>
    if not results:
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue
                course = cells[0].get_text(strip=True)
                req    = cells[-1].get_text(strip=True)
                if course:
                    results.append({"course": course[:80], "entry_req": req or "N/A"})

    return results
