"""
Exchange Rates parser – used only in TEST_MODE.

API: https://open.er-api.com/v6/latest/GBP  (free, no key, updates daily)

Clearing page analog:
  Currency code (USD, EUR, JPY…) = Course name
  Rate vs GBP                    = Entry requirement (a number that changes)

When a rate changes between polls, the change detector fires exactly as it
will when a university lowers its UCAS points during clearing.
"""

import requests

BASE_URL = "https://open.er-api.com/v6/latest/GBP"

# Only track these currencies to keep the sheet manageable
TRACK = [
    "USD", "EUR", "JPY", "CAD", "AUD", "CHF", "CNY",
    "INR", "MXN", "BRL", "SGD", "HKD", "NOK", "SEK",
    "DKK", "NZD", "ZAR", "KRW", "TRY", "THB",
]


def extract(soup=None) -> list[dict]:          # soup arg ignored – we use the API directly
    r = requests.get(BASE_URL, timeout=15)
    r.raise_for_status()
    data = r.json()

    if data.get("result") != "success":
        return []

    rates = data.get("rates", {})
    results = []
    for code in TRACK:
        if code in rates:
            # Format rate to 6 sig figs, same style as UCAS points: "1.2754"
            rate_str = f"{rates[code]:.6g}"
            results.append({
                "course":    f"{code} / GBP",
                "entry_req": rate_str,
            })
    return results
