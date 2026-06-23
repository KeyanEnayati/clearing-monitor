"""
clearing_simulation.py – realistic UK clearing stand-in for TEST_MODE.

Three simulated competitor universities, 8 courses each.
Entry requirements follow real clearing patterns (grades drop as universities
fill spaces) so the pipeline looks identical to the real production use case.

How the timing works:
  - On first call the current time is stored as the "epoch".
  - Every 15-minute polling period, some courses drop a grade.
  - Courses drop at staggered times so changes arrive 1-3 per poll,
    not all at once – just like real clearing.
  - Changes start appearing from the 2nd poll onwards.
"""

import json
import time
from pathlib import Path

_EPOCH_FILE = Path(__file__).parent.parent / "data" / "sim_epoch.json"


def _get_epoch() -> int:
    if _EPOCH_FILE.exists():
        return json.loads(_EPOCH_FILE.read_text(encoding="utf-8"))["epoch"]
    # Set epoch to 25 min ago so first grade drop is detected on 2nd poll
    e = int(time.time()) - 25 * 60
    _EPOCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _EPOCH_FILE.write_text(json.dumps({"epoch": e}), encoding="utf-8")
    return e


def _grade(period: int, grades: list, stagger: int) -> str:
    """Return the grade for this poll period, respecting the course stagger."""
    idx = min(max(0, period - stagger) // 2, len(grades) - 1)
    return grades[idx]


# ── Simulated university course data ─────────────────────────────────────────
# Each entry: (Course name, [grade high→low, as clearing progresses], stagger)
# Stagger = number of periods before this course first drops a grade.
# At 15-min intervals with stagger 0-7, changes arrive spread across 8 polls.

_DATA = {
    "CLEARING_UNI_A": [
        # A-level grade requirements (drop each clearing cycle)
        ("BSc Computing",          ["ABB", "BBB", "BBC", "BCC", "CCC"],  0),
        ("BA Business Management", ["BBB", "BBC", "BCC", "CCC"],         1),
        ("BSc Nursing (Adult)",    ["ABB", "BBB", "BBC"],                 2),
        ("LLB Law",                ["AAB", "ABB", "BBB", "BBC"],          3),
        ("BEng Civil Engineering", ["ABB", "BBB", "BBC", "BCC"],          4),
        ("BSc Psychology",         ["BBB", "BBC", "BCC", "CCC"],          5),
        ("BA Marketing",           ["BBC", "BCC", "CCC"],                 6),
        ("BA Education Studies",   ["BCC", "CCC", "CCD"],                 7),
    ],
    "CLEARING_UNI_B": [
        # UCAS points (drop by 8 pts each clearing cycle)
        ("BSc Computer Science",           ["128 UCAS pts", "120 UCAS pts", "112 UCAS pts", "104 UCAS pts"], 0),
        ("BA International Business",      ["120 UCAS pts", "112 UCAS pts", "104 UCAS pts", "96 UCAS pts"],  1),
        ("BEng Mechanical Engineering",    ["136 UCAS pts", "128 UCAS pts", "120 UCAS pts"],                 2),
        ("BSc Sport Science",              ["112 UCAS pts", "104 UCAS pts", "96 UCAS pts"],                  3),
        ("BA Criminology",                 ["104 UCAS pts", "96 UCAS pts",  "88 UCAS pts"],                  4),
        ("BSc Pharmacy (MPharm)",          ["AAB",           "ABB",          "BBB"],                         5),
        ("BA Graphic Design",              ["96 UCAS pts",  "88 UCAS pts",  "80 UCAS pts"],                  6),
        ("BA Media Studies",               ["88 UCAS pts",  "80 UCAS pts",  "72 UCAS pts"],                  7),
    ],
    "CLEARING_UNI_C": [
        # Mixed: A-levels, BTEC, descriptive requirements
        ("BSc Data Science",           ["ABB",                          "BBB",                        "BBC",                   "BCC"], 0),
        ("BA Accounting & Finance",    ["ABB",                          "BBB",                        "BBC"],                          1),
        ("BEng Electronic Engineering",["BBB",                          "BBC",                        "BCC",                   "CCC"], 2),
        ("BSc Biomedical Science",     ["BBB",                          "BBC",                        "BCC"],                          3),
        ("BSc Architecture",           ["ABB",                          "BBB",                        "BBC"],                          4),
        ("BA Fashion Design",          ["Distinction Merit Merit",       "Merit Merit Distinction",    "Merit Merit Merit"],            5),
        ("BSc Environmental Science",  ["BBC",                          "BCC",                        "CCC"],                          6),
        ("BA Music Technology",        ["Distinction Distinction Merit", "Distinction Merit Merit",    "Merit Merit Distinction"],      7),
    ],
}


def get_courses(uni_key: str) -> list[dict]:
    period = max(0, (int(time.time()) - _get_epoch()) // 900)
    return [
        {"course": name, "entry_req": _grade(period, grades, stagger)}
        for name, grades, stagger in _DATA[uni_key]
    ]
