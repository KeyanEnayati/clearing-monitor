"""
scraper.py – fetches and parses clearing data from university websites.

For each university the pipeline is:
  1. Load page  (requests or Selenium depending on requires_js)
  2. Extract    (HTML table parser → generic block parser → fallback)
  3. Return     list of {"course": str, "entry_req": str}
"""

import time
import logging
import re
import importlib
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Selenium lazy-import (only used when requires_js=True)
# ---------------------------------------------------------------------------
_driver = None

def _get_driver(headless: bool = True):
    global _driver
    if _driver is not None:
        return _driver
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    # Selenium 4.6+ has a built-in driver manager that automatically downloads
    # the ChromeDriver version that matches the installed Chrome — no external
    # webdriver-manager needed, no version mismatch possible.
    _driver = webdriver.Chrome(options=opts)
    return _driver


def quit_driver():
    global _driver
    if _driver:
        _driver.quit()
        _driver = None


# ---------------------------------------------------------------------------
# Page fetching
# ---------------------------------------------------------------------------

def _fetch_html_static(url: str, timeout: int) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def _fetch_html_js(url: str, timeout: int, wait: int, headless: bool) -> str:
    driver = _get_driver(headless)
    driver.set_page_load_timeout(timeout)
    driver.get(url)
    time.sleep(wait)
    return driver.page_source


def fetch_page(uni_cfg: dict, timeout: int, js_wait: int, headless: bool) -> str:
    url = uni_cfg["clearing_url"]
    if uni_cfg.get("requires_js", False):
        log.info("  Fetching (Selenium): %s", url)
        return _fetch_html_js(url, timeout, js_wait, headless)
    log.info("  Fetching (requests): %s", url)
    return _fetch_html_static(url, timeout)


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _header_matches(text: str, hints: list[str]) -> bool:
    t = text.lower().strip()
    return any(h in t for h in hints)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# Strategy 1 – HTML <table> with recognisable column headers
def _extract_from_tables(
    soup: BeautifulSoup,
    table_selector: Optional[str],
    course_hint: str,
    req_hint: str,
) -> list[dict]:
    results = []
    tables = (
        soup.select(table_selector)
        if table_selector
        else soup.find_all("table")
    )

    course_hints = [course_hint, "course", "programme", "subject", "title"]
    req_hints    = [req_hint, "ucas", "tariff", "entry", "points", "grade", "requirement"]

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Find header row
        header_row = rows[0]
        headers = [_clean(th.get_text()) for th in header_row.find_all(["th", "td"])]
        if not headers:
            continue

        # Identify course and requirement column indices
        course_idx = req_idx = None
        for i, h in enumerate(headers):
            if course_idx is None and _header_matches(h, course_hints):
                course_idx = i
            if req_idx is None and _header_matches(h, req_hints):
                req_idx = i

        if course_idx is None:
            continue  # Cannot identify course column in this table
        if req_idx is None:
            # Use last column as fallback
            req_idx = len(headers) - 1

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(course_idx, req_idx):
                continue
            course = _clean(cells[course_idx].get_text())
            req    = _clean(cells[req_idx].get_text())
            if course:
                results.append({"course": course, "entry_req": req or "N/A"})

    return results


# Strategy 2 – structured <div>/<li> blocks (accordion / card layout)
def _extract_from_blocks(soup: BeautifulSoup) -> list[dict]:
    results = []
    req_pattern = re.compile(
        r"(ucas\s*(points|tariff)|entry\s*req|minimum\s*grade|tariff|points\s*required)",
        re.IGNORECASE,
    )

    # Look for elements that contain a UCAS/points label near a number
    for block in soup.find_all(["li", "div", "article", "section"]):
        text = _clean(block.get_text(separator=" "))
        if not req_pattern.search(text):
            continue

        # Try to pull course name from a heading inside the block
        heading = block.find(re.compile(r"^h[1-6]$"))
        course = _clean(heading.get_text()) if heading else ""

        # Try to extract points value (e.g. "112 points" or "BCC")
        points_match = re.search(
            r"(\d{2,3}\s*(?:UCAS\s*)?(?:points|tariff)|[A-E]{3}|[A-E]\*{0,1}[A-E]{2})",
            text,
            re.IGNORECASE,
        )
        req = points_match.group(0) if points_match else text[:80]

        if course or req:
            results.append({
                "course": course or "Unknown Course",
                "entry_req": _clean(req),
            })

    return results


# Strategy 3 – custom per-university parser in parsers/<key>.py
# If the parser module exposes extract(soup) it gets HTML; if it takes no args
# (like exchange_rates) it fetches its own data internally.
def _extract_custom(uni_key: str, soup: BeautifulSoup) -> list[dict]:
    module_path = f"parsers.{uni_key.lower()}"
    try:
        mod = importlib.import_module(module_path)
        import inspect
        sig = inspect.signature(mod.extract)
        # Parsers that fetch their own data (e.g. JSON APIs) take no arguments
        if len(sig.parameters) == 0:
            return mod.extract()
        return mod.extract(soup)
    except ModuleNotFoundError:
        log.warning("  No custom parser found at %s", module_path)
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scrape_university(uni_key: str, uni_cfg: dict, cfg) -> list[dict]:
    """
    Returns list of dicts: [{"course": str, "entry_req": str}, ...]
    Returns [] on complete failure.
    """
    for attempt in range(1, cfg.RETRY_ATTEMPTS + 1):
        try:
            method = uni_cfg.get("scrape_method", "table")

            # JSON-API parsers fetch their own data – skip HTML fetch entirely
            if method == "custom":
                module_path = f"parsers.{uni_key.lower()}"
                try:
                    mod = importlib.import_module(module_path)
                    import inspect
                    sig = inspect.signature(mod.extract)
                    if len(sig.parameters) == 0:
                        data = mod.extract()
                        if data:
                            log.info("  Extracted %d courses from %s", len(data), uni_cfg.get("name", uni_key))
                            return data
                        # fall through to HTML fetch if empty
                except ModuleNotFoundError:
                    pass  # will be caught below

            html = fetch_page(uni_cfg, cfg.PAGE_LOAD_TIMEOUT, cfg.JS_WAIT_SECONDS, cfg.HEADLESS)
            soup = BeautifulSoup(html, "lxml")

            if method == "custom":
                data = _extract_custom(uni_key, soup)
            elif method == "list":
                data = _extract_from_blocks(soup)
            else:  # default: table
                data = _extract_from_tables(
                    soup,
                    uni_cfg.get("table_selector"),
                    uni_cfg.get("course_col_hint", "course"),
                    uni_cfg.get("req_col_hint", "ucas"),
                )
                # Fall back to block extraction if table found nothing
                if not data:
                    log.info("  Table extraction empty, trying block extraction")
                    data = _extract_from_blocks(soup)

            if data:
                log.info("  Extracted %d courses from %s", len(data), uni_cfg["name"])
                return data

            log.warning("  No data extracted from %s (attempt %d)", uni_cfg["name"], attempt)

        except Exception as exc:
            log.error("  Error scraping %s (attempt %d): %s", uni_cfg["name"], attempt, exc)

        if attempt < cfg.RETRY_ATTEMPTS:
            log.info("  Retrying in %ds...", cfg.RETRY_DELAY)
            time.sleep(cfg.RETRY_DELAY)

    return []
