"""
generate_dashboard.py – reads change history + current state and writes index.html.

Run:  python generate_dashboard.py
Output: index.html  (served by GitHub Pages, or just open locally in a browser)

The page auto-refreshes every 30 minutes so staff can leave the tab open.
"""

import json
from datetime import datetime
from pathlib import Path

import config as cfg

CHANGES_LOG = cfg.DATA_DIR / "changes_log.json"
STATE_DIR   = cfg.DATA_DIR / "state"
HEARTBEAT   = cfg.BASE_DIR / "heartbeat.json"
OUTPUT      = cfg.BASE_DIR / "index.html"


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _fmt_dt(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d %b %H:%M")
    except Exception:
        return iso_str or "—"


# ── HTML builders ─────────────────────────────────────────────────────────────

def _course_table_html(course: str, changes: list, current_req: str) -> str:
    """One mini-table for a single course (mirrors the Excel layout)."""
    # Header row: [Course name] [timestamp1] [timestamp2] ...
    header_cells = f'<th class="cn">{course}</th>'
    for ch in changes:
        header_cells += f'<th class="ts">{_fmt_dt(ch["detected_at"])}</th>'

    # Data row: [current state] [req after change1] [req after change2] ...
    current_label = f"Now: {current_req}" if current_req else "—"
    data_cells = f'<td class="lbl">{current_label}</td>'
    for ch in changes:
        kind    = ch.get("kind", "changed")
        new_req = ch.get("new_req", "")
        old_req = ch.get("old_req", "")
        tip     = f' title="Was: {old_req}"' if old_req else ""
        css     = "dc new" if kind == "new" else "dc"
        data_cells += f'<td class="{css}"{tip}>{new_req}</td>'

    return (
        f'<div class="ct">'
        f'<table>'
        f'<tr class="hr">{header_cells}</tr>'
        f'<tr class="dr">{data_cells}</tr>'
        f'</table>'
        f'</div>'
    )


def _university_section_html(uni_key: str, uni_name: str) -> str:
    changes_by_uni = _load_json(CHANGES_LOG)
    state          = _load_json(STATE_DIR / f"{uni_key}.json")
    uni_changes    = changes_by_uni.get(uni_key, [])

    # Group changes by course, preserving time order
    by_course: dict[str, list] = {}
    for ch in uni_changes:
        by_course.setdefault(ch["course"], []).append(ch)

    all_courses = sorted(set(by_course) | set(state))

    if not all_courses:
        tables_html = "<p class='nd'>No data yet – waiting for first change detection.</p>"
    else:
        tables_html = ""
        for course in all_courses:
            current_req = state.get(course, {}).get("req", "") if isinstance(state, dict) else ""
            tables_html += _course_table_html(course, by_course.get(course, []), current_req)

    return (
        f'<section class="uni">'
        f'<h2>{uni_name}</h2>'
        f'<div class="tc">{tables_html}</div>'
        f'</section>'
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def generate():
    hb        = _load_json(HEARTBEAT)
    last_poll = hb.get("last_poll_at", "Never")
    poll_num  = hb.get("poll_number", 0)
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    sections = ""
    for uni_key, uni_cfg in cfg.UNIVERSITIES.items():
        sections += _university_section_html(uni_key, uni_cfg["name"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="1800">
  <title>Clearing Monitor</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f7;color:#222}}
    header{{background:#7B2D8B;color:#fff;padding:1rem 2rem}}
    header h1{{font-size:1.4rem;margin-bottom:.3rem}}
    header .meta{{font-size:.82rem;opacity:.85}}
    main{{padding:1.5rem 2rem}}
    .uni{{margin-bottom:2.5rem}}
    .uni h2{{color:#7B2D8B;border-bottom:2px solid #7B2D8B;padding-bottom:.4rem;margin-bottom:1rem;font-size:1.15rem}}
    .tc{{display:flex;flex-wrap:wrap;gap:1rem}}
    .ct{{overflow-x:auto}}
    table{{border-collapse:collapse;font-size:.85rem;white-space:nowrap;border:1px solid #ccc}}
    .hr th{{background:#7B2D8B;color:#fff;padding:.45rem .9rem;text-align:center;font-weight:600}}
    .cn{{background:#5A1F6E!important;text-align:left!important;min-width:180px}}
    .ts{{min-width:90px}}
    .dr td{{padding:.45rem .9rem;border-top:1px solid #ddd;text-align:center}}
    .lbl{{background:#f3e8f7;text-align:left!important;font-style:italic;color:#555}}
    .dc{{background:#fff}}
    .dc.new{{background:#e8f7ee;color:#2a7a4b}}
    .nd{{color:#999;font-style:italic;padding:.5rem}}
    footer{{text-align:center;padding:1rem;font-size:.78rem;color:#aaa;border-top:1px solid #e0e0e0;margin-top:2rem}}
  </style>
</head>
<body>
  <header>
    <h1>Clearing Monitor – Live Entry Requirements</h1>
    <div class="meta">
      Last poll: {last_poll} &nbsp;|&nbsp; Poll #{poll_num} &nbsp;|&nbsp;
      Dashboard generated: {now_str}
      &nbsp;(auto-refreshes every 30 min)
    </div>
  </header>
  <main>
    {sections}
  </main>
  <footer>Monitored by Aston University &mdash; updates automatically every poll cycle</footer>
</body>
</html>"""

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Dashboard written -> {OUTPUT}")


if __name__ == "__main__":
    generate()
