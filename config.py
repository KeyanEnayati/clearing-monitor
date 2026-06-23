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
        # Exchange rates vs GBP – updates daily, no browser needed, works on GitHub.
        # Currency code = Course name.  Rate = Entry requirement (numeric, changes daily).
        # Perfect structural analog: a named list of things each with a changing number.
        "EXCHANGE_RATES": {
            "name": "Currency Rates vs GBP (TEST)",
            "clearing_url": "https://open.er-api.com/v6/latest/GBP",
            "scrape_method": "custom",   # uses parsers/exchange_rates.py
            "requires_js":  False,
            "notes":        "No browser needed. Rates update daily – inject_change.py for instant demo.",
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
