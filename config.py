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
    # Three simulated competitor universities with realistic UK clearing data.
    # Course names, grade structures, and drop patterns mirror real clearing.
    # Requirements drop every ~30 min per course, staggered so 1-3 changes
    # appear per poll – identical behaviour to the real production system.
    UNIVERSITIES = {
        "CLEARING_UNI_A": {
            "name": "Birmingham City University (BCU)",
            "clearing_url": "simulation://clearing_uni_a",
            "scrape_method": "custom",   # parsers/clearing_uni_a.py
            "requires_js":  False,
            "notes":        "8 BCU courses with full A-level/GCSE requirements. Drops every ~30 min.",
        },
        "CLEARING_UNI_B": {
            "name": "Coventry University",
            "clearing_url": "simulation://clearing_uni_b",
            "scrape_method": "custom",   # parsers/clearing_uni_b.py
            "requires_js":  False,
            "notes":        "8 Coventry courses with full UCAS tariff requirements. Drops every ~30 min.",
        },
        "CLEARING_UNI_C": {
            "name": "De Montfort University (DMU)",
            "clearing_url": "simulation://clearing_uni_c",
            "scrape_method": "custom",   # parsers/clearing_uni_c.py
            "requires_js":  False,
            "notes":        "8 DMU courses, mixed A-level/BTEC/portfolio requirements. Drops every ~30 min.",
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
