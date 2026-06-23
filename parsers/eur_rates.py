"""
EUR Exchange Rates parser – used in TEST_MODE as "Competitor C".

API: https://api.frankfurter.app/latest  (free, no key, updates daily)

Clearing page analog:
  Currency pair (GBP vs EUR…) = Course name
  Exchange rate               = Entry requirement
"""

import requests

BASE_URL = "https://api.frankfurter.app/latest"

TRACK = [
    "GBP", "USD", "JPY", "CHF", "AUD", "CAD",
    "CNY", "INR", "MXN", "BRL", "SGD", "NOK",
    "SEK", "DKK", "NZD",
]


def extract() -> list[dict]:
    r = requests.get(BASE_URL, params={"from": "EUR", "to": ",".join(TRACK)}, timeout=15)
    r.raise_for_status()
    data = r.json()

    rates = data.get("rates", {})
    results = []
    for code in TRACK:
        if code in rates:
            results.append({
                "course":    f"{code} / EUR",
                "entry_req": f"{rates[code]:.6g}",
            })
    return results
