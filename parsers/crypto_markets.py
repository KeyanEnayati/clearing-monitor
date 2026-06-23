"""
Crypto Markets parser – used in TEST_MODE as "Competitor B".

API: https://api.coingecko.com/api/v3/coins/markets  (free, no key)

Clearing page analog:
  Coin name (Bitcoin, Ethereum…) = Course name
  Current GBP price              = Entry requirement (changes every ~5 min)

This gives rapid real changes – ideal for demonstrating the detection pipeline
without waiting for daily exchange-rate updates.
"""

import requests

API_URL = "https://api.coingecko.com/api/v3/coins/markets"

PARAMS = {
    "vs_currency": "gbp",
    "order":       "market_cap_desc",
    "per_page":    15,
    "page":        1,
    "sparkline":   "false",
}


def extract() -> list[dict]:
    r = requests.get(API_URL, params=PARAMS, timeout=20)
    r.raise_for_status()
    coins = r.json()

    results = []
    for coin in coins:
        name  = coin.get("name", "")
        price = coin.get("current_price")
        if name and price is not None:
            results.append({
                "course":    name,
                "entry_req": f"GBP {price:,.2f}",
            })
    return results
