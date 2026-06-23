"""
Clearing Monitor – Configuration
=================================
TEST_MODE = True   → ClinicalTrials.gov public API (real live data, no browser,
                     runs anywhere including GitHub Actions). Uses UK recruiting
                     trials as a stand-in for clearing courses: eligibility
                     criteria text = entry requirements, status changes = changes.
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
    # Real live data from ClinicalTrials.gov public API.
    # Three categories of UK recruiting clinical trials, each becoming one tab.
    # Trial name         → course name
    # Eligibility text   → entry requirement (full descriptive paragraphs)
    # Status change      → new column (identical pipeline to clearing day)
    # Trial appearing    → "new course" row
    # Trial completing   → "removed course" row
    UNIVERSITIES = {
        "TRIALS_CANCER": {
            "name": "UK Cancer Trials",
            "clearing_url": "https://clinicaltrials.gov/api/v2/studies",
            "scrape_method": "custom",   # parsers/trials_cancer.py
            "requires_js":  False,
            "notes":        "Up to 8 UK recruiting cancer trials. Changes: status, eligibility amendments.",
        },
        "TRIALS_CARDIO": {
            "name": "UK Cardiovascular Trials",
            "clearing_url": "https://clinicaltrials.gov/api/v2/studies",
            "scrape_method": "custom",   # parsers/trials_cardio.py
            "requires_js":  False,
            "notes":        "Up to 8 UK recruiting cardiovascular trials.",
        },
        "TRIALS_DIABETES": {
            "name": "UK Diabetes Trials",
            "clearing_url": "https://clinicaltrials.gov/api/v2/studies",
            "scrape_method": "custom",   # parsers/trials_diabetes.py
            "requires_js":  False,
            "notes":        "Up to 8 UK recruiting diabetes trials.",
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
