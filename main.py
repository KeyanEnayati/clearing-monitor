"""
main.py – Clearing Monitor (change-detection, continuous polling)

The script runs forever, wakes every POLL_INTERVAL_MINUTES, scrapes every
configured university, and writes to Excel ONLY when something changed –
with the exact timestamp of detection.

After every poll it writes heartbeat.json so the health-check tool can
confirm the script is alive and hasn't missed any cycles.

Usage
-----
  python main.py              continuous loop (normal use)
  python main.py --once       single poll then exit
  python main.py --uni KEY    only poll one university
  python main.py --reset KEY  wipe saved state (re-baselines on next poll)
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import config as cfg
from scraper import scrape_university, quit_driver
from change_detector import detect
from state_manager import load_state, apply_changes
from excel_logger import log_changes, init_workbook

# ---------------------------------------------------------------------------
# Logging – both console and daily file
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            cfg.LOGS_DIR / f"monitor_{datetime.now():%Y%m%d}.log",
            encoding="utf-8",
        ),
    ],
)
log = logging.getLogger(__name__)

HEARTBEAT_FILE = cfg.BASE_DIR / "heartbeat.json"
CHANGES_LOG    = cfg.DATA_DIR / "changes_log.json"
_poll_count = 0


# ---------------------------------------------------------------------------
# Changes log – appended on every detected change so generate_dashboard.py
# and GitHub Actions can read the full history without parsing Excel
# ---------------------------------------------------------------------------
def _write_changes_log(uni_key: str, changes: list):
    try:
        all_changes = json.loads(CHANGES_LOG.read_text(encoding="utf-8")) if CHANGES_LOG.exists() else {}
    except Exception:
        all_changes = {}

    bucket = all_changes.setdefault(uni_key, [])
    for ch in changes:
        if ch.get("kind") in ("changed", "new"):
            dt = ch.get("detected_at", datetime.now())
            dt_str = dt.isoformat(timespec="seconds") if isinstance(dt, datetime) else str(dt)
            bucket.append({
                "course":      ch["course"],
                "kind":        ch["kind"],
                "old_req":     ch.get("old_req", "") or "",
                "new_req":     ch.get("new_req", ""),
                "detected_at": dt_str,
            })

    CHANGES_LOG.write_text(json.dumps(all_changes, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Heartbeat – written after every poll so health-check can verify the script
# is alive and no cycles were skipped
# ---------------------------------------------------------------------------
def _write_heartbeat(changes_this_poll: int):
    global _poll_count
    _poll_count += 1
    data = {
        "status":              "running",
        "last_poll_at":        datetime.now().isoformat(timespec="seconds"),
        "poll_number":         _poll_count,
        "poll_interval_min":   cfg.POLL_INTERVAL_MINUTES,
        "changes_this_poll":   changes_this_poll,
        "universities":        list(cfg.UNIVERSITIES.keys()),
    }
    HEARTBEAT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Single poll – scrapes all universities, logs any changes
# ---------------------------------------------------------------------------
def poll(uni_filter: str | None = None) -> int:
    """Returns number of changes recorded across all universities."""
    universities = cfg.UNIVERSITIES
    if uni_filter:
        if uni_filter not in universities:
            log.error("University key '%s' not found in config.", uni_filter)
            return 0
        universities = {uni_filter: universities[uni_filter]}

    total_changes = 0

    for uni_key, uni_cfg_entry in universities.items():
        log.info("Polling: %s", uni_cfg_entry["name"])

        scraped = scrape_university(uni_key, uni_cfg_entry, cfg)
        if not scraped:
            log.warning("  No data returned – skipping.")
            continue

        last_state = load_state(cfg.DATA_DIR, uni_key)

        if not last_state:
            # First ever poll for this university: build baseline silently.
            # Nothing is written to Excel on first poll – we need a "before"
            # state before we can detect a "change".
            log.info(
                "  First poll – recording %d courses as baseline. "
                "Changes will be logged from the next poll onwards.",
                len(scraped),
            )
            apply_changes(
                cfg.DATA_DIR, uni_key,
                [{"kind": "new", "course": c["course"], "new_req": c["entry_req"]}
                 for c in scraped],
            )
            continue

        changes = detect(scraped, last_state)

        if not changes:
            log.info("  No changes detected.")
            continue

        log_changes(cfg.EXCEL_FILE, uni_key, changes, cfg.DATA_DIR)
        _write_changes_log(uni_key, changes)
        apply_changes(cfg.DATA_DIR, uni_key, changes)
        total_changes += len(changes)

    return total_changes


# ---------------------------------------------------------------------------
# Continuous loop
# ---------------------------------------------------------------------------
def run_loop(uni_filter: str | None = None):
    interval = cfg.POLL_INTERVAL_MINUTES * 60

    log.info("=" * 60)
    log.info("Clearing Monitor  –  started %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("Poll interval : %d minutes", cfg.POLL_INTERVAL_MINUTES)
    log.info("Universities  : %s", ", ".join(cfg.UNIVERSITIES))
    log.info("Excel output  : %s", cfg.EXCEL_FILE)
    log.info("=" * 60)

    init_workbook(cfg.EXCEL_FILE, cfg.UNIVERSITIES)

    while True:
        log.info("─" * 40)
        log.info("Poll #%d  at %s", _poll_count + 1, datetime.now().strftime("%H:%M:%S"))
        try:
            n = poll(uni_filter)
            _write_heartbeat(n)
            if n:
                log.info("  %d change(s) written to Excel.", n)
            log.info("  Next poll in %d min.", cfg.POLL_INTERVAL_MINUTES)
        except Exception as exc:
            log.error("Unexpected error: %s", exc, exc_info=True)
            _write_heartbeat(0)

        time.sleep(interval)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Clearing Monitor")
    p.add_argument("--once",  action="store_true", help="Single poll then exit")
    p.add_argument("--uni",   type=str,            help="Only poll this university key")
    p.add_argument("--reset", type=str, metavar="KEY",
                   help="Clear saved state for a university (re-baselines on next poll)")
    args = p.parse_args()

    try:
        if args.reset:
            f = cfg.DATA_DIR / "state" / f"{args.reset}.json"
            if f.exists():
                f.unlink()
                log.info("State cleared for '%s'.", args.reset)
            else:
                log.info("No state file found for '%s'.", args.reset)

        elif args.once:
            init_workbook(cfg.EXCEL_FILE, cfg.UNIVERSITIES)
            n = poll(uni_filter=args.uni)
            _write_heartbeat(n)

        else:
            run_loop(uni_filter=args.uni)

    except KeyboardInterrupt:
        log.info("Stopped by user.")
    finally:
        quit_driver()


if __name__ == "__main__":
    main()
