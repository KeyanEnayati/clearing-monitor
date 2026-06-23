"""
Clearing Monitor – Configuration
=================================
TEST_MODE = True   → exchange rate API (free, no browser, runs anywhere including GitHub)
TEST_MODE = False  → real university clearing pages
"""

from pathlib import Path

BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
LOGS_DIR  = BASE_DIR / "logs"
EXCEL_FILE = BASE_DIR / "clearing_data.xlsx"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

TEST_MODE = True   # flip to False for real clearing

# Poll every N minutes. 15 is good for clearing day.
POLL_INTERVAL_MINUTES = 15

if TEST_MODE:
    UNIVERSITIES = {
        # ── Test source 1: GBP exchange rates (updates daily) ──────────────
        "EXCHANGE_RATES": {
            "name": "Competitor A – GBP Exchange Rates",
            "clearing_url": "https://open.er-api.com/v6/latest/GBP",
            "scrape_method": "custom",   # parsers/exchange_rates.py
            "requires_js":  False,
            "notes":        "20 currencies vs GBP. Updates once daily.",
        },
        # ── Test source 2: Crypto market prices (updates every ~5 min) ─────
        # Best for live demo – prices change frequently, just like UCAS points
        # drop during clearing as universities fill spaces.
        "CRYPTO_MARKETS": {
            "name": "Competitor B – Crypto Markets",
            "clearing_url": "https://api.coingecko.com/api/v3/coins/markets?vs_currency=gbp",
            "scrape_method": "custom",   # parsers/crypto_markets.py
            "requires_js":  False,
            "notes":        "Top 15 coins in GBP. Updates every ~5 min.",
        },
        # ── Test source 3: EUR exchange rates (updates daily) ──────────────
        "EUR_RATES": {
            "name": "Competitor C – EUR Exchange Rates",
            "clearing_url": "https://api.frankfurter.app/latest?from=EUR",
            "scrape_method": "custom",   # parsers/eur_rates.py
            "requires_js":  False,
            "notes":        "15 currencies vs EUR. Updates once daily.",
        },
    }
else:
    UNIVERSITIES = {
        "BCU": {
            "name": "Birmingham City University",
            "clearing_url": "https://www.bcu.ac.uk/clearing",
            "scrape_method": "table",
            "requires_js":  True,
            "table_selector": None,
            "course_col_hint": "course",
            "req_col_hint":    "ucas",
            "notes": "",
        },
        # add more universities here …
    }

HEADLESS           = True
PAGE_LOAD_TIMEOUT  = 45
JS_WAIT_SECONDS    = 5
RETRY_ATTEMPTS     = 2
RETRY_DELAY        = 8
LOG_LEVEL          = "INFO"
HEADER_BG          = "7B2D8B"
HEADER_FG          = "FFFFFF"
