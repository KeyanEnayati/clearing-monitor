"""
generate_dashboard.py – reads change history + current state → writes index.html

Table layout (mirrors the Excel sheet exactly):
  Header row:  [Course Name]  [First Seen: dd Mon HH:MM]  [Change 1 time]  [Change 2 time] …
  Data row:    [Entry Req]    [initial requirement]         [new req]        [new req] …

Every course always shows its first recorded value.
Additional columns appear only when a change is detected.

Run:  python generate_dashboard.py
Output: index.html  (served by GitHub Pages, or open locally in any browser)
"""

import json
from datetime import datetime
from pathlib import Path

import config as cfg

CHANGES_LOG = cfg.DATA_DIR / "changes_log.json"
STATE_DIR   = cfg.DATA_DIR / "state"
HEARTBEAT   = cfg.BASE_DIR / "heartbeat.json"
OUTPUT      = cfg.BASE_DIR / "index.html"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_json(path: Path):
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


# ── Table builder ─────────────────────────────────────────────────────────────

def _course_table(course: str, changes: list, state_info: dict) -> str:
    """
    Build one mini-table for a single course.

    Header:  [Course Name] [First Seen timestamp] [Change 1 ts] [Change 2 ts] …
    Data:    [Entry Req]   [initial requirement]  [new req 1]   [new req 2]   …
    """
    first_seen  = state_info.get("first_seen", "") if state_info else ""
    current_req = state_info.get("req", "")        if state_info else ""

    # Initial requirement: if changes exist it's the old_req before the first change
    initial_req = changes[0]["old_req"] if changes else current_req

    # ── Header row ────────────────────────────────────────────────────────────
    header = f'<th class="cn">{course}</th>'
    header += f'<th class="ts">{_fmt_dt(first_seen)}</th>'
    for ch in changes:
        header += f'<th class="ts">{_fmt_dt(ch["detected_at"])}</th>'

    # ── Data row ──────────────────────────────────────────────────────────────
    data = '<td class="lbl">Entry Requirement</td>'
    data += f'<td class="dc">{initial_req or "—"}</td>'
    for ch in changes:
        data += f'<td class="dc chg">{ch.get("new_req", "—")}</td>'

    return (
        f'<div class="ct">'
        f'<table>'
        f'<tr class="hr">{header}</tr>'
        f'<tr class="dr">{data}</tr>'
        f'</table>'
        f'</div>'
    )


# ── Tab content ───────────────────────────────────────────────────────────────

def _tab_content(uni_key: str) -> str:
    state      = _load_json(STATE_DIR / f"{uni_key}.json")
    all_ch     = _load_json(CHANGES_LOG)
    uni_ch     = all_ch.get(uni_key, [])

    # Group changes by course (preserve time order within each course)
    by_course: dict[str, list] = {}
    for ch in uni_ch:
        by_course.setdefault(ch["course"], []).append(ch)

    # All courses: union of state keys and courses that have changes
    all_courses = sorted(set(state) | set(by_course))

    if not all_courses:
        return "<p class='nd'>No data yet – waiting for first successful poll.</p>"

    tables = ""
    for course in all_courses:
        tables += _course_table(
            course,
            by_course.get(course, []),
            state.get(course) if isinstance(state, dict) else None,
        )

    return f'<div class="tc">{tables}</div>'


# ── Page assembly ─────────────────────────────────────────────────────────────

def generate():
    hb        = _load_json(HEARTBEAT)
    last_poll = hb.get("last_poll_at", "Never")
    poll_num  = hb.get("poll_number", 0)
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # Build tab buttons and panels
    tab_btns    = ""
    tab_panels  = ""
    for i, (uni_key, uni_cfg) in enumerate(cfg.UNIVERSITIES.items()):
        active   = " active"       if i == 0 else ""
        display  = ""              if i == 0 else ' style="display:none"'
        tab_btns   += f'<button class="tb{active}" onclick="showTab(\'{uni_key}\',this)">{uni_cfg["name"]}</button>\n'
        tab_panels += f'<div id="{uni_key}" class="tp"{display}>{_tab_content(uni_key)}</div>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta http-equiv="refresh" content="900">
  <title>Clearing Monitor</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f7;color:#222}}

    /* ── Header ── */
    header{{background:#7B2D8B;color:#fff;padding:1rem 2rem}}
    header h1{{font-size:1.4rem;margin-bottom:.3rem}}
    .meta{{font-size:.82rem;opacity:.85}}

    /* ── Tab bar ── */
    .tabs{{display:flex;flex-wrap:wrap;background:#5A1F6E;padding:0 1.5rem}}
    .tb{{
      background:none;border:none;border-bottom:3px solid transparent;
      color:rgba(255,255,255,.65);padding:.7rem 1.4rem;cursor:pointer;
      font-size:.88rem;font-family:inherit;transition:color .15s,border-color .15s
    }}
    .tb:hover{{color:#fff}}
    .tb.active{{color:#fff;border-bottom-color:#fff}}

    /* ── Tab panels ── */
    .tp{{padding:1.5rem 2rem}}

    /* ── Course table grid ── */
    .tc{{display:flex;flex-wrap:wrap;gap:1.2rem}}
    .ct{{overflow-x:auto}}

    /* ── Mini table ── */
    table{{border-collapse:collapse;font-size:.85rem;white-space:nowrap;
           border:1px solid #ccc;border-radius:4px;overflow:hidden}}

    /* Header row */
    .hr th{{background:#7B2D8B;color:#fff;padding:.45rem 1rem;
            text-align:center;font-weight:600}}
    .cn{{background:#5A1F6E!important;text-align:left!important;
         min-width:200px;font-size:.9rem}}
    .ts{{min-width:110px;font-size:.78rem;opacity:.9}}

    /* Data row */
    .dr td{{padding:.45rem 1rem;border-top:1px solid #ddd;text-align:center}}
    .lbl{{background:#f3e8f7;text-align:left!important;
          color:#5A1F6E;font-weight:600;font-size:.8rem;letter-spacing:.02em}}
    .dc{{background:#fff;font-weight:500}}
    .chg{{background:#fff8e1}}   /* changed cells: subtle warm highlight */

    .nd{{color:#999;font-style:italic;padding:.5rem}}

    footer{{text-align:center;padding:1rem;font-size:.78rem;color:#aaa;
            border-top:1px solid #e0e0e0;margin-top:2rem}}
  </style>
</head>
<body>
  <header>
    <h1>Clearing Monitor – Live Entry Requirements</h1>
    <div class="meta">
      Last poll: {last_poll} &nbsp;|&nbsp; Poll #{poll_num} &nbsp;|&nbsp;
      Generated: {now_str} &nbsp;(auto-refreshes every 15 min)
    </div>
  </header>

  <nav class="tabs">
{tab_btns}  </nav>

{tab_panels}
  <footer>Monitored by Aston University – updates automatically every poll cycle</footer>

  <script>
    function showTab(id, btn) {{
      document.querySelectorAll('.tp').forEach(el => el.style.display = 'none');
      document.querySelectorAll('.tb').forEach(el => el.classList.remove('active'));
      document.getElementById(id).style.display = 'block';
      btn.classList.add('active');
    }}
  </script>
</body>
</html>"""

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Dashboard written -> {OUTPUT}")


if __name__ == "__main__":
    generate()
