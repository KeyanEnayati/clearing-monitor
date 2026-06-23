"""
Custom parser for Worldometers COVID table.
URL: https://www.worldometers.info/coronavirus/

Why this is a good clearing-page analog:
  Country name   →  Course name
  New Cases today  →  Entry requirement (a number that changes through the day
                       as countries report – just like UCAS points changing
                       during clearing)

The "New Cases" column starts blank/empty for most countries early in the day
and fills in as each country submits its daily update. When a value appears
or changes, our change detector fires and logs it with the exact timestamp.
"""

from bs4 import BeautifulSoup


def extract(soup: BeautifulSoup) -> list[dict]:
    results = []

    table = soup.find("table", id="main_table_countries_today")
    if not table:
        return results

    tbody = table.find("tbody")
    if not tbody:
        return results

    for row in tbody.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue

        # col 1 = Country name
        country_cell = cells[1]
        country = country_cell.get_text(strip=True)

        # Skip continent summary rows (they have no country link)
        if not country or country in ("", "World"):
            continue

        # col 3 = New Cases today  (the column that changes throughout the day)
        new_cases = cells[3].get_text(strip=True)

        # col 2 = Total Cases  (cumulative – rarely changes within a day)
        total_cases = cells[2].get_text(strip=True)

        # Build a descriptive requirement string (mirrors how clearing pages
        # show grade + points together)
        if new_cases and new_cases not in ("+0", "0"):
            req = f"New today: {new_cases}  |  Total: {total_cases}"
        else:
            req = f"Total: {total_cases}"

        results.append({
            "course":    country,
            "entry_req": req,
        })

    return results
