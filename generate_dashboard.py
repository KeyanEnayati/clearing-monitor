"""
generate_dashboard.py – reads change history + current state → writes index.html

Layout per university tab:
  One full-width row per course, each independently scrollable left/right.

  ┌─────────────────────────┬──────────────────┬──────────────────┬─────────────────┐
  │ BSc (Hons) Computing    │  23 Jun 23:16    │  24 Jun 09:30    │  24 Jun 10:00   │
  ├─────────────────────────┼──────────────────┼──────────────────┼─────────────────┤
  │ Entry Requirement       │ BBB or 120 UCAS  │ BBC or 112 UCAS  │ CLEARING – BCC  │
  │                         │ tariff points…   │ tariff points…   │ call admissions │
  └─────────────────────────┴──────────────────┴──────────────────┴─────────────────┘

  ┌─────────────────────────┬──────────────────┐
  │ LLB Law                 │  23 Jun 23:16    │   (no changes yet – one column)
  ├─────────────────────────┼──────────────────┤
  │ Entry Requirement       │ ABB or 128 UCAS… │
  └─────────────────────────┴──────────────────┘

  The course-name column is sticky so it stays visible as you scroll right.
  Each row is self-contained; adding more timestamps never affects other rows.
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


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Row builder ───────────────────────────────────────────────────────────────

def _course_row(course: str, changes: list, state_info: dict) -> str:
    """
    One full-width scrollable row for a single course.

    Header:  [Course Name sticky] | [First Seen ts]  | [Change ts 1]  | [Change ts 2] …
    Data:    [Entry Requirement]  | [initial req]     | [new req 1]    | [new req 2]   …

    The first column (course name + "Entry Requirement" label) is sticky so
    it stays on screen when the user scrolls right through many timestamps.
    """
    first_seen  = state_info.get("first_seen", "") if state_info else ""
    current_req = state_info.get("req", "")        if state_info else ""
    initial_req = changes[0]["old_req"] if changes else current_req

    # Header cells
    hcells = f'<th class="cn sticky-col">{_escape(course)}</th>'
    hcells += f'<th class="ts">{_fmt_dt(first_seen)}</th>'
    for ch in changes:
        hcells += f'<th class="ts">{_fmt_dt(ch["detected_at"])}</th>'

    # Data cells
    dcells = '<td class="lbl sticky-col">Entry Requirement</td>'
    dcells += f'<td class="dc">{_escape(initial_req) if initial_req else "—"}</td>'
    for ch in changes:
        dcells += f'<td class="dc chg">{_escape(ch.get("new_req", "—"))}</td>'

    return (
        f'<div class="course-row">'
        f'<div class="scroll-wrap">'
        f'<table>'
        f'<thead><tr class="hr">{hcells}</tr></thead>'
        f'<tbody><tr class="dr">{dcells}</tr></tbody>'
        f'</table>'
        f'</div>'
        f'</div>'
    )


# ── Tab content ───────────────────────────────────────────────────────────────

def _tab_content(uni_key: str) -> str:
    state  = _load_json(STATE_DIR / f"{uni_key}.json")
    all_ch = _load_json(CHANGES_LOG)
    uni_ch = all_ch.get(uni_key, [])

    by_course: dict[str, list] = {}
    for ch in uni_ch:
        by_course.setdefault(ch["course"], []).append(ch)

    # Preserve the order courses appear in the state file (poll order)
    # rather than sorting alphabetically
    all_courses: list[str] = []
    if isinstance(state, dict):
        all_courses = list(state.keys())
    for c in by_course:
        if c not in all_courses:
            all_courses.append(c)

    if not all_courses:
        return "<p class='nd'>No data yet – waiting for first successful poll.</p>"

    rows = ""
    for course in all_courses:
        rows += _course_row(
            course,
            by_course.get(course, []),
            state.get(course) if isinstance(state, dict) else None,
        )
    return rows


# ── Page assembly ─────────────────────────────────────────────────────────────

def generate():
    hb        = _load_json(HEARTBEAT)
    last_poll = hb.get("last_poll_at", "Never")
    poll_num  = hb.get("poll_number", 0)
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    tab_btns   = ""
    tab_panels = ""
    for i, (uni_key, uni_cfg) in enumerate(cfg.UNIVERSITIES.items()):
        active  = " active" if i == 0 else ""
        display = ""        if i == 0 else ' style="display:none"'
        name    = _escape(uni_cfg["name"])
        tab_btns   += (
            f'    <button class="tb{active}" '
            f'onclick="showTab(\'{uni_key}\',this)">{name}</button>\n'
        )
        tab_panels += (
            f'<div id="{uni_key}" class="tp"{display}>\n'
            f'{_tab_content(uni_key)}\n'
            f'</div>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta http-equiv="refresh" content="900">
  <title>Clearing Monitor – Aston University</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f2f2f5;
      color: #222;
      font-size: 14px;
    }}

    /* ── Header ── */
    header {{
      background: #7B2D8B;
      color: #fff;
      padding: 1rem 1.5rem;
    }}
    header h1 {{ font-size: 1.25rem; margin-bottom: 0.25rem; }}
    .meta {{ font-size: 0.78rem; opacity: 0.82; }}

    /* ── Tabs ── */
    .tabs {{
      display: flex;
      flex-wrap: wrap;
      background: #5A1F6E;
      padding: 0 1rem;
      gap: 0;
    }}
    .tb {{
      background: none;
      border: none;
      border-bottom: 3px solid transparent;
      color: rgba(255,255,255,0.6);
      padding: 0.65rem 1.25rem;
      cursor: pointer;
      font-size: 0.85rem;
      font-family: inherit;
      font-weight: 500;
      transition: color 0.15s, border-color 0.15s;
      white-space: nowrap;
    }}
    .tb:hover  {{ color: #fff; }}
    .tb.active {{ color: #fff; border-bottom-color: #fff; }}

    /* ── Tab panel ── */
    .tp {{
      padding: 1.25rem 1.5rem;
    }}

    /* ── Course row wrapper ── */
    .course-row {{
      margin-bottom: 1.25rem;
      border: 1px solid #d0d0d8;
      border-radius: 5px;
      overflow: hidden;          /* clip rounded corners */
      box-shadow: 0 1px 3px rgba(0,0,0,.06);
    }}

    /* This div is what actually scrolls left/right */
    .scroll-wrap {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}

    /* ── Table ── */
    table {{
      border-collapse: collapse;
      width: 100%;
      min-width: max-content;   /* never shrink below content width */
    }}

    /* ── Header row ── */
    .hr th {{
      background: #7B2D8B;
      color: #fff;
      padding: 0.5rem 1rem;
      text-align: center;
      font-weight: 600;
      font-size: 0.82rem;
      white-space: nowrap;
      border-right: 1px solid rgba(255,255,255,0.15);
    }}
    .hr th:last-child {{ border-right: none; }}

    /* Course name – left-aligned, wider, sticky */
    .cn {{
      text-align: left !important;
      background: #5A1F6E !important;
      min-width: 240px;
      max-width: 280px;
      white-space: normal;
      font-size: 0.88rem;
      font-weight: 700;
      line-height: 1.4;
      border-right: 2px solid rgba(255,255,255,0.25) !important;
    }}

    /* Timestamp column headers */
    .ts {{
      min-width: 270px;
      font-size: 0.78rem;
      opacity: 0.9;
      font-weight: 500;
    }}

    /* ── Data row ── */
    .dr td {{
      padding: 0.6rem 1rem;
      border-top: none;
      border-right: 1px solid #e0e0e8;
      text-align: left;
      vertical-align: top;
      line-height: 1.55;
    }}
    .dr td:last-child {{ border-right: none; }}

    /* "Entry Requirement" label cell – sticky, matches header colour */
    .lbl {{
      background: #f0e4f7 !important;
      color: #5A1F6E;
      font-weight: 700;
      font-size: 0.75rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      white-space: nowrap;
      min-width: 240px;
      max-width: 280px;
      border-right: 2px solid #d8b8e8 !important;
    }}

    /* Normal data cell – wraps long requirement text */
    .dc {{
      background: #ffffff;
      white-space: normal;
      word-break: break-word;
      min-width: 270px;
      max-width: 400px;
      font-size: 0.83rem;
    }}

    /* Changed cells – warm yellow tint so they stand out */
    .chg {{ background: #fffbea; }}

    /* Sticky first column (course name + label) */
    .sticky-col {{
      position: sticky;
      left: 0;
      z-index: 2;
    }}

    /* "No data" placeholder */
    .nd {{ color: #999; font-style: italic; padding: 0.75rem; }}

    footer {{
      text-align: center;
      padding: 1rem;
      font-size: 0.75rem;
      color: #aaa;
      border-top: 1px solid #e0e0e0;
      margin-top: 1.5rem;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Clearing Monitor – Live Entry Requirements</h1>
    <div class="meta">
      Last poll: {last_poll} &nbsp;|&nbsp; Poll #{poll_num} &nbsp;|&nbsp;
      Generated: {now_str} &nbsp;&nbsp;(page auto-refreshes every 15 min)
    </div>
  </header>

  <nav class="tabs">
{tab_btns}  </nav>

{tab_panels}
  <footer>Monitored by Aston University &mdash; updates automatically on every poll cycle</footer>

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
