"""
run_clearing_day_test.py
========================
Simulates a full clearing day (09:00 – 11:00) in under 5 seconds.

What it tests:
  - Multiple timestamp columns accumulating on each course row
  - Courses APPEARING mid-session (university unlocks new spaces)
  - Courses DISAPPEARING mid-session (spaces filled, removed from search)
  - Requirements DROPPING progressively as clearing progresses
  - Excel + dashboard both rendering the full history correctly

Run:
  python run_clearing_day_test.py

After it finishes, open index.html in any browser.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Imports from the monitor codebase
# ---------------------------------------------------------------------------
import config as cfg
from change_detector import detect
from state_manager import load_state, apply_changes
from excel_logger import log_changes, init_workbook

# ---------------------------------------------------------------------------
# Step 1: Wipe all state so we start completely fresh
# ---------------------------------------------------------------------------
def _reset():
    state_dir = cfg.DATA_DIR / "state"
    for f in state_dir.glob("CLEARING_UNI_*.json"):
        f.unlink()
    cl = cfg.DATA_DIR / "changes_log.json"
    if cl.exists():
        cl.unlink()
    if cfg.EXCEL_FILE.exists():
        cfg.EXCEL_FILE.unlink()
    for f in (cfg.DATA_DIR / "sim_epoch.json",):
        if f.exists():
            f.unlink()
    print("  State, changes log, and Excel cleared.")

# ---------------------------------------------------------------------------
# Step 2: Define six polls across a typical clearing day
#         (timestamp, university key, scraped course list)
#
# Shows: initial snapshot → requirements drop → courses appear/disappear
# ---------------------------------------------------------------------------
POLLS = [

    # ── 09:00 – clearing opens ─────────────────────────────────────────────
    ("2026-08-14T09:00:00", "CLEARING_UNI_A", [
        {"course": "BSc (Hons) Computing",
         "entry_req": "BBB or 120 UCAS tariff points. GCSE Mathematics B/5 and English Language C/4."},
        {"course": "LLB Law",
         "entry_req": "ABB or 128 UCAS tariff points. No specific A-levels. GCSE English Language B/5."},
        {"course": "BA (Hons) Business Management",
         "entry_req": "BCC or 104 UCAS tariff points. GCSE Maths and English C/4. BTEC MMM accepted."},
        {"course": "BSc (Hons) Nursing (Adult)",
         "entry_req": "BBC or 112 UCAS tariff points. Science A-level preferred. "
                      "Care experience required. Enhanced DBS check. Occupational Health assessment."},
        {"course": "BEng (Hons) Civil Engineering",
         "entry_req": "BBB or 120 UCAS tariff points. Mathematics A-level required. GCSE Maths B/5."},
    ]),
    ("2026-08-14T09:00:00", "CLEARING_UNI_B", [
        {"course": "BSc (Hons) Computer Science",
         "entry_req": "ABB or 136 UCAS tariff points. Mathematics A-level grade B or above. GCSE Maths 5."},
        {"course": "BA (Hons) International Business",
         "entry_req": "BBB or 120 UCAS tariff points. No specific A-levels. GCSE English Language and Maths 4."},
        {"course": "BSc (Hons) Sport and Exercise Science",
         "entry_req": "BBC or 112 UCAS tariff points. PE or Biology preferred. GCSE Maths 4."},
        {"course": "MPharm Pharmacy (4 years)",
         "entry_req": "AAB or 152 UCAS tariff points. Chemistry A-level at grade A required. Interview required."},
    ]),
    ("2026-08-14T09:00:00", "CLEARING_UNI_C", [
        {"course": "BSc (Hons) Data Science",
         "entry_req": "BBB or 120 UCAS tariff points. Mathematics A-level strongly recommended. GCSE Maths 5."},
        {"course": "BA (Hons) Accounting and Finance",
         "entry_req": "BBB or 120 UCAS tariff points. Maths or Business A-level preferred. GCSE Maths B/5."},
        {"course": "BEng (Hons) Electronic Engineering",
         "entry_req": "BBB or 120 UCAS tariff points. Mathematics and Physics A-levels required. GCSE Maths B/5."},
        {"course": "BSc (Hons) Architecture (ARB/RIBA Part 1)",
         "entry_req": "ABB or 128 UCAS tariff points. Portfolio of creative/technical work required. GCSE English and Maths C/4."},
    ]),

    # ── 09:30 – first requirements drop ────────────────────────────────────
    ("2026-08-14T09:30:00", "CLEARING_UNI_A", [
        {"course": "BSc (Hons) Computing",          # CHANGED ↓
         "entry_req": "BBC or 112 UCAS tariff points. GCSE Mathematics B/5 and English C/4. "
                      "Non-standard qualifications considered – call 0121 331 5595."},
        {"course": "LLB Law",                        # unchanged
         "entry_req": "ABB or 128 UCAS tariff points. No specific A-levels. GCSE English Language B/5."},
        {"course": "BA (Hons) Business Management",  # CHANGED ↓
         "entry_req": "CCC or 96 UCAS tariff points. GCSE Maths and English C/4. BTEC MMP accepted."},
        {"course": "BSc (Hons) Nursing (Adult)",     # CHANGED – science A-level no longer mandatory
         "entry_req": "BBC or 112 UCAS tariff points. Science A-level no longer mandatory for clearing. "
                      "Relevant care experience required. Enhanced DBS and Occupational Health check."},
        {"course": "BEng (Hons) Civil Engineering",  # unchanged
         "entry_req": "BBB or 120 UCAS tariff points. Mathematics A-level required. GCSE Maths B/5."},
    ]),
    ("2026-08-14T09:30:00", "CLEARING_UNI_B", [
        {"course": "BSc (Hons) Computer Science",    # CHANGED ↓
         "entry_req": "BBB or 120 UCAS tariff points. Mathematics A-level required. GCSE Maths 4."},
        {"course": "BA (Hons) International Business",  # CHANGED ↓
         "entry_req": "BBC or 112 UCAS tariff points. GCSE English Language and Maths 4."},
        {"course": "BSc (Hons) Sport and Exercise Science",  # CHANGED ↓
         "entry_req": "BCC or 104 UCAS tariff points. GCSE English Language and Maths 4."},
        {"course": "MPharm Pharmacy (4 years)",      # CHANGED ↓
         "entry_req": "ABB or 136 UCAS tariff points. Chemistry A-level required. Interview required."},
    ]),
    ("2026-08-14T09:30:00", "CLEARING_UNI_C", [
        {"course": "BSc (Hons) Data Science",        # CHANGED ↓
         "entry_req": "BBC or 112 UCAS tariff points. Mathematics A-level recommended but not required. GCSE Maths 4."},
        {"course": "BA (Hons) Accounting and Finance",  # CHANGED ↓
         "entry_req": "BBC or 112 UCAS tariff points. Maths or Business background preferred. GCSE Maths B/5."},
        {"course": "BEng (Hons) Electronic Engineering",  # CHANGED ↓
         "entry_req": "BBC or 112 UCAS tariff points. Mathematics A-level required. GCSE Maths 5."},
        {"course": "BSc (Hons) Architecture (ARB/RIBA Part 1)",  # unchanged
         "entry_req": "ABB or 128 UCAS tariff points. Portfolio required. GCSE English and Maths C/4."},
    ]),

    # ── 10:00 – clearing vacancies declared, new courses appear ────────────
    ("2026-08-14T10:00:00", "CLEARING_UNI_A", [
        {"course": "BSc (Hons) Computing",
         "entry_req": "CLEARING VACANCY – BCC or 104 UCAS tariff points. GCSE Mathematics essential. "
                      "Call BCU Clearing: 0121 331 5595."},
        {"course": "LLB Law",                        # CHANGED ↓
         "entry_req": "BBB or 120 UCAS tariff points. GCSE English Language B/5."},
        # BA Business Management REMOVED – spaces filled, no longer in UCAS search
        {"course": "BSc (Hons) Nursing (Adult)",
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Care experience required. "
                      "Enhanced DBS check required. Call 0121 331 5595."},
        {"course": "BEng (Hons) Civil Engineering",  # CHANGED ↓
         "entry_req": "BBC or 112 UCAS tariff points. Mathematics A-level required. GCSE Maths 4."},
        {"course": "BSc (Hons) Psychology",          # NEW – university opens additional spaces
         "entry_req": "BBC or 112 UCAS tariff points. GCSE English Language and Maths C/4. "
                      "Psychology or Biology A-level desirable."},
    ]),
    ("2026-08-14T10:00:00", "CLEARING_UNI_B", [
        {"course": "BSc (Hons) Computer Science",
         "entry_req": "CLEARING VACANCY – BBC or 112 tariff points. Mathematics A-level required. "
                      "Call Coventry Clearing: 02477 655 645."},
        # International Business REMOVED – spaces filled
        {"course": "BSc (Hons) Sport and Exercise Science",
         "entry_req": "CLEARING VACANCY – CCC or 96 tariff points. Call 02477 655 645."},
        {"course": "MPharm Pharmacy (4 years)",      # CHANGED ↓
         "entry_req": "BBB or 120 UCAS tariff points. Chemistry A-level required. Interview required."},
        {"course": "BA (Hons) Criminology",          # NEW course appears
         "entry_req": "BCC or 104 UCAS tariff points. No specific A-levels. GCSE English Language and Maths 4."},
    ]),
    ("2026-08-14T10:00:00", "CLEARING_UNI_C", [
        {"course": "BSc (Hons) Data Science",
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. GCSE Maths essential. "
                      "Call DMU Clearing: 0116 250 6070."},
        {"course": "BA (Hons) Accounting and Finance",
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Call 0116 250 6070."},
        {"course": "BEng (Hons) Electronic Engineering",
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Mathematics A-level required. Call 0116 250 6070."},
        {"course": "BSc (Hons) Architecture (ARB/RIBA Part 1)",  # CHANGED ↓
         "entry_req": "BBB or 120 UCAS tariff points. Portfolio required. Creative or scientific A-level preferred."},
        {"course": "BSc (Hons) Environmental Science",  # NEW course appears
         "entry_req": "BBC or 112 UCAS tariff points. Science A-level preferred. GCSE Maths and English C/4."},
    ]),

    # ── 10:30 – final stages, limited spaces ───────────────────────────────
    ("2026-08-14T10:30:00", "CLEARING_UNI_A", [
        {"course": "BSc (Hons) Computing",
         "entry_req": "CLEARING – limited spaces remaining. 96 UCAS tariff points or above. "
                      "GCSE Mathematics required. Call NOW: 0121 331 5595."},
        {"course": "LLB Law",
         "entry_req": "CLEARING VACANCY – BBC or 112 tariff points. GCSE English Language C/4 accepted. "
                      "All A-levels welcome. Call 0121 331 5595."},
        {"course": "BSc (Hons) Nursing (Adult)",     # unchanged
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Care experience required. "
                      "Enhanced DBS check required. Call 0121 331 5595."},
        {"course": "BEng (Hons) Civil Engineering",
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Mathematics A-level required. "
                      "GCSE Maths 4. Call 0121 331 5595."},
        {"course": "BSc (Hons) Psychology",          # CHANGED ↓
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Open to all A-level combinations. "
                      "GCSE English and Maths required. Call 0121 331 5595."},
    ]),
    ("2026-08-14T10:30:00", "CLEARING_UNI_B", [
        {"course": "BSc (Hons) Computer Science",
         "entry_req": "CLEARING – final spaces. BCC or equivalent. Mathematics A-level required. "
                      "Call 02477 655 645."},
        # Sport and Exercise Science REMOVED – spaces filled
        {"course": "MPharm Pharmacy (4 years)",
         "entry_req": "CLEARING VACANCY – BBB or 120 tariff points. Chemistry A-level required. "
                      "Interview required. Call 02477 655 645."},
        {"course": "BA (Hons) Criminology",          # CHANGED ↓
         "entry_req": "CCC or 96 UCAS tariff points. GCSE English Language and Maths 4."},
    ]),
    ("2026-08-14T10:30:00", "CLEARING_UNI_C", [
        # Data Science REMOVED – spaces filled
        {"course": "BA (Hons) Accounting and Finance",
         "entry_req": "CLEARING – final spaces. CCC or 96 tariff points. Call 0116 250 6070."},
        {"course": "BEng (Hons) Electronic Engineering",
         "entry_req": "CLEARING – final spaces. BBC or equivalent. Mathematics required. Call 0116 250 6070."},
        {"course": "BSc (Hons) Architecture (ARB/RIBA Part 1)",
         "entry_req": "CLEARING VACANCY – BBC or 112 tariff points. Portfolio required. Call 0116 250 6070."},
        {"course": "BSc (Hons) Environmental Science",  # CHANGED ↓
         "entry_req": "CLEARING VACANCY – BCC or 104 tariff points. Science A-level welcomed. Call 0116 250 6070."},
        {"course": "BA (Hons) Fashion Design",       # NEW – opened late
         "entry_req": "CCC or 96 UCAS tariff points. Art or Design A-level. Portfolio required. GCSE English C/4."},
    ]),
]


# ---------------------------------------------------------------------------
# Step 3: Process each poll – detect changes, write Excel + log
# ---------------------------------------------------------------------------
def run():
    print("\nClearing Day Test – Birmingham City University / Coventry / DMU")
    print("=" * 65)
    print("\nStep 1: Resetting all state...")
    _reset()
    init_workbook(cfg.EXCEL_FILE, cfg.UNIVERSITIES)

    # Track "virtual" state between polls (not persisted to disk mid-test)
    virtual_state: dict[str, dict] = {k: {} for k in cfg.UNIVERSITIES}
    changes_log_path = cfg.DATA_DIR / "changes_log.json"

    for poll_ts, uni_key, scraped in POLLS:
        poll_time = datetime.fromisoformat(poll_ts)
        uni_name  = cfg.UNIVERSITIES.get(uni_key, {}).get("name", uni_key)

        # Load persisted state for this university
        state = load_state(cfg.DATA_DIR, uni_key)

        if not state:
            # First poll for this university: build baseline silently
            print(f"\n  [{poll_time.strftime('%H:%M')}] {uni_name}")
            print(f"    Baseline: {len(scraped)} courses recorded.")
            apply_changes(
                cfg.DATA_DIR, uni_key,
                [{"kind": "new", "course": c["course"], "new_req": c["entry_req"]}
                 for c in scraped],
            )
            continue

        # Subsequent polls: detect changes
        changes = detect(scraped, state)

        # Override detected_at with the simulated poll time
        for ch in changes:
            ch["detected_at"] = poll_time

        if changes:
            kinds = {"changed": 0, "new": 0, "removed": 0}
            for ch in changes:
                kinds[ch["kind"]] += 1
            print(f"\n  [{poll_time.strftime('%H:%M')}] {uni_name}")
            print(f"    {kinds['changed']} changed, {kinds['new']} new, {kinds['removed']} removed")

            # Write to Excel
            log_changes(cfg.EXCEL_FILE, uni_key, changes, cfg.DATA_DIR)

            # Write to changes_log.json (for dashboard)
            all_cl = {}
            if changes_log_path.exists():
                try:
                    all_cl = json.loads(changes_log_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            bucket = all_cl.setdefault(uni_key, [])
            for ch in changes:
                if ch.get("kind") in ("changed", "new"):
                    dt = ch["detected_at"]
                    bucket.append({
                        "course":      ch["course"],
                        "kind":        ch["kind"],
                        "old_req":     ch.get("old_req", "") or "",
                        "new_req":     ch.get("new_req", ""),
                        "detected_at": dt.isoformat(timespec="seconds"),
                    })
            changes_log_path.write_text(
                json.dumps(all_cl, indent=2), encoding="utf-8"
            )

            # Update persisted state
            apply_changes(cfg.DATA_DIR, uni_key, changes)
        else:
            print(f"  [{poll_time.strftime('%H:%M')}] {uni_name} – no changes")

    print("\nStep 3: Generating dashboard...")
    # Write a realistic heartbeat so the dashboard header looks right
    import config as cfg2
    hb = {
        "status": "running",
        "last_poll_at": "2026-08-14T10:30:00",
        "poll_number": 8,
        "poll_interval_min": 15,
        "changes_this_poll": 5,
        "universities": list(cfg2.UNIVERSITIES.keys()),
    }
    (cfg2.BASE_DIR / "heartbeat.json").write_text(
        json.dumps(hb, indent=2), encoding="utf-8"
    )

    from generate_dashboard import generate
    generate()

    print("\n" + "=" * 65)
    print("Test complete. Open index.html in your browser to inspect.")
    print("Look for:")
    print("  - Multiple timestamp columns per course row")
    print("  - REMOVED courses (no longer listed after spaces fill)")
    print("  - NEW courses (appeared mid-clearing)")
    print("  - Horizontal scroll on long rows")
    print("=" * 65)


if __name__ == "__main__":
    run()
