"""
demo_layout.py – writes a realistic fake clearing dataset directly to Excel
so you can see exactly what the layout looks like without waiting for
a live scrape.

Simulates BCU with 5 courses across 6 hours of clearing,
each changing at different times and by different amounts.
"""

from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from excel_logger import log_changes, init_workbook
import config as cfg

# Fake university
FAKE_UNI = "BCU_DEMO"

FAKE_CHANGES = [
    # ------------------------------------------------------------------
    # 09:00 – Clearing opens.  All courses listed with opening requirements.
    # ------------------------------------------------------------------
    {
        "course":       "Accounting and Finance BSc",
        "old_req":      None,
        "new_req":      "ABB | 128 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 9, 0, 0),
        "kind":         "new",
    },
    {
        "course":       "Business Management BA",
        "old_req":      None,
        "new_req":      "BBB | 120 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 9, 0, 0),
        "kind":         "new",
    },
    {
        "course":       "Computer Science BSc",
        "old_req":      None,
        "new_req":      "ABB | 128 UCAS points | Grade B Maths",
        "detected_at":  datetime(2026, 8, 14, 9, 0, 0),
        "kind":         "new",
    },
    {
        "course":       "Marketing BA",
        "old_req":      None,
        "new_req":      "BBC | 112 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 9, 0, 0),
        "kind":         "new",
    },
    {
        "course":       "Law LLB",
        "old_req":      None,
        "new_req":      "AAB | 136 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 9, 0, 0),
        "kind":         "new",
    },

    # ------------------------------------------------------------------
    # 10:47 – First reductions (quiet morning, spaces filling slowly)
    # ------------------------------------------------------------------
    {
        "course":       "Accounting and Finance BSc",
        "old_req":      "ABB | 128 UCAS points",
        "new_req":      "ABB | 120 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 10, 47, 0),
        "kind":         "changed",
    },
    {
        "course":       "Marketing BA",
        "old_req":      "BBC | 112 UCAS points",
        "new_req":      "BBC | 104 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 10, 47, 0),
        "kind":         "changed",
    },

    # ------------------------------------------------------------------
    # 12:15 – Lunch rush – several courses drop simultaneously
    # ------------------------------------------------------------------
    {
        "course":       "Accounting and Finance BSc",
        "old_req":      "ABB | 120 UCAS points",
        "new_req":      "BBB | 112 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 12, 15, 0),
        "kind":         "changed",
    },
    {
        "course":       "Business Management BA",
        "old_req":      "BBB | 120 UCAS points",
        "new_req":      "BBC | 112 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 12, 15, 0),
        "kind":         "changed",
    },
    {
        "course":       "Computer Science BSc",
        "old_req":      "ABB | 128 UCAS points | Grade B Maths",
        "new_req":      "ABB | 120 UCAS points | Grade B Maths",
        "detected_at":  datetime(2026, 8, 14, 12, 15, 0),
        "kind":         "changed",
    },
    {
        "course":       "Law LLB",
        "old_req":      "AAB | 136 UCAS points",
        "new_req":      "ABB | 128 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 12, 15, 0),
        "kind":         "changed",
    },

    # ------------------------------------------------------------------
    # 14:03 – Afternoon – aggressive drops on slower-filling courses
    # ------------------------------------------------------------------
    {
        "course":       "Marketing BA",
        "old_req":      "BBC | 104 UCAS points",
        "new_req":      "BCC | 96 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 14, 3, 0),
        "kind":         "changed",
    },
    {
        "course":       "Business Management BA",
        "old_req":      "BBC | 112 UCAS points",
        "new_req":      "BCC | 96 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 14, 3, 0),
        "kind":         "changed",
    },

    # ------------------------------------------------------------------
    # 16:30 – Late afternoon – final push
    # ------------------------------------------------------------------
    {
        "course":       "Accounting and Finance BSc",
        "old_req":      "BBB | 112 UCAS points",
        "new_req":      "BBC | 104 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 16, 30, 0),
        "kind":         "changed",
    },
    {
        "course":       "Computer Science BSc",
        "old_req":      "ABB | 120 UCAS points | Grade B Maths",
        "new_req":      "BBB | 112 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 16, 30, 0),
        "kind":         "changed",
    },
    {
        "course":       "Law LLB",
        "old_req":      "ABB | 128 UCAS points",
        "new_req":      "ABB | 120 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 16, 30, 0),
        "kind":         "changed",
    },

    # ------------------------------------------------------------------
    # 17:55 – End of day – Marketing scraping barrel
    # ------------------------------------------------------------------
    {
        "course":       "Marketing BA",
        "old_req":      "BCC | 96 UCAS points",
        "new_req":      "CCC | 80 UCAS points",
        "detected_at":  datetime(2026, 8, 14, 17, 55, 0),
        "kind":         "changed",
    },
]


def run():
    path = cfg.BASE_DIR / "clearing_data.xlsx"
    init_workbook(path, {FAKE_UNI: {}})

    # Group changes by detected_at so we process each "poll" together
    from collections import defaultdict
    by_time = defaultdict(list)
    for ch in FAKE_CHANGES:
        by_time[ch["detected_at"]].append(ch)

    for ts in sorted(by_time):
        batch = by_time[ts]
        log_changes(path, FAKE_UNI, batch, cfg.DATA_DIR)
        print(f"  {ts.strftime('%H:%M')}  – recorded {len(batch)} change(s)")

    print(f"\nDemo complete. Open: {path}")


if __name__ == "__main__":
    run()
