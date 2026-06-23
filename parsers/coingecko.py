"""
Custom parser for CoinGecko (https://www.coingecko.com/)
Used only in TEST_MODE to verify the full pipeline.

CoinGecko renders its table via React, so Selenium fetches the page.
We look for the main coin-ranking table and extract:
  coin name  → "course"
  USD price  → "entry_req"
"""

import re
from bs4 import BeautifulSoup


def extract(soup: BeautifulSoup) -> list[dict]:
    results = []

    # CoinGecko renders a <table> with data-coin-name attributes on rows,
    # or uses a tbody with tr rows.  We try multiple strategies.

    # Strategy A: look for the main sortable table
    table = soup.find("table", class_=re.compile(r"sort", re.I))
    if not table:
        # Strategy B: any table that contains "$" price values
        for t in soup.find_all("table"):
            if "$" in t.get_text():
                table = t
                break

    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue

            # Coin name: typically in 2nd or 3rd cell, look for a span/div
            # with the coin name (not the ticker)
            name_cell = cells[2] if len(cells) > 2 else cells[1]
            name_candidates = name_cell.find_all(
                ["span", "div", "a", "p"],
                class_=re.compile(r"(name|coin|title|tw-)", re.I),
            )
            if name_candidates:
                coin_name = name_candidates[0].get_text(strip=True)
            else:
                # CoinGecko concatenates name+ticker in one cell (e.g. "BitcoinBTC").
                # Split by detecting where the all-caps ticker starts at the end.
                raw = name_cell.get_text(separator=" ", strip=True)
                parts = raw.split()
                # Drop rank numbers and 2-6 char all-caps tickers
                name_parts = [
                    p for p in parts
                    if not p.isdigit() and not (p.isupper() and 2 <= len(p) <= 6)
                ]
                if name_parts:
                    coin_name = " ".join(name_parts[:4])
                else:
                    # Fallback: strip trailing uppercase ticker with regex
                    coin_name = re.sub(r"[A-Z0-9_]{2,6}$", "", raw).strip() or raw[:40]

            # Price: look for "$" formatted value
            price = ""
            for cell in cells[3:6]:
                text = cell.get_text(strip=True)
                if "$" in text or re.search(r"\d+\.\d+", text):
                    price = text.replace("​", "").strip()
                    break

            if coin_name and coin_name not in ("", "#"):
                results.append({
                    "course":    coin_name[:60],
                    "entry_req": price or "N/A",
                })

        # Limit to top 50 coins for a clean test
        return results[:50]

    # Fallback: scrape span/div pairs with coin name + price pattern
    price_pattern = re.compile(r"\$[\d,]+\.?\d*")
    for item in soup.find_all(attrs={"data-coin-symbol": True}):
        name = item.get_text(strip=True)[:60]
        parent = item.parent
        price_el = parent.find(string=price_pattern) if parent else None
        price = price_el.strip() if price_el else "N/A"
        if name:
            results.append({"course": name, "entry_req": price})

    return results[:50]
