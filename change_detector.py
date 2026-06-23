"""
change_detector.py – compares a fresh scrape against last-known state.

Returns a list of change dicts:
  {
    "kind":     "changed" | "new" | "removed",
    "course":   str,
    "old_req":  str | None,
    "new_req":  str,
    "detected_at": datetime,
  }
"""

import re
import logging
from datetime import datetime

log = logging.getLogger(__name__)


def detect(scraped: list[dict], last_state: dict) -> list[dict]:
    """
    scraped    – list of {"course": str, "entry_req": str}
    last_state – dict of {course_name: {"req": str, ...}}

    Returns list of change events (empty = nothing changed).
    """
    now     = datetime.now()
    changes = []

    scraped_map = {
        item["course"].strip(): item["entry_req"].strip()
        for item in scraped
        if item.get("course", "").strip()
    }

    # Changed or new courses
    for course, new_req in scraped_map.items():
        if course not in last_state:
            changes.append({
                "kind":         "new",
                "course":       course,
                "old_req":      None,
                "new_req":      new_req,
                "detected_at":  now,
            })
        else:
            old_req = last_state[course]["req"]
            if _normalise(old_req) != _normalise(new_req):
                changes.append({
                    "kind":         "changed",
                    "course":       course,
                    "old_req":      old_req,
                    "new_req":      new_req,
                    "detected_at":  now,
                })

    # Removed courses (was in state, no longer scraped)
    for course, info in last_state.items():
        if course not in scraped_map:
            changes.append({
                "kind":         "removed",
                "course":       course,
                "old_req":      info["req"],
                "new_req":      "REMOVED",
                "detected_at":  now,
            })

    if changes:
        kinds = {"changed": 0, "new": 0, "removed": 0}
        for c in changes:
            kinds[c["kind"]] += 1
        log.info(
            "  Changes detected: %d changed, %d new, %d removed",
            kinds["changed"], kinds["new"], kinds["removed"],
        )
    return changes


def direction(old_req: str | None, new_req: str) -> str:
    """
    Returns a short label describing the direction of change:
      "DROPPED"  – numeric requirement fell  (easier to get in)
      "RAISED"   – numeric requirement rose  (harder to get in)
      "NEW"      – course appeared for first time
      "REMOVED"  – course no longer listed
      "CHANGED"  – text changed but no numeric comparison possible
    """
    if old_req is None:
        return "NEW"
    if new_req == "REMOVED":
        return "REMOVED"
    op = _to_points(old_req)
    np_ = _to_points(new_req)
    if op is not None and np_ is not None:
        if np_ < op:
            return "DROPPED"
        if np_ > op:
            return "RAISED"
    return "CHANGED"


def time_gap(last_changed_iso: str | None, detected_at: datetime) -> str:
    """Human-readable gap since the previous change, e.g. '2h 15m'."""
    if not last_changed_iso:
        return "-"
    try:
        prev = datetime.fromisoformat(last_changed_iso)
        delta = detected_at - prev
        total_mins = int(delta.total_seconds() // 60)
        if total_mins < 1:
            return "< 1m"
        h, m = divmod(total_mins, 60)
        if h == 0:
            return f"{m}m"
        return f"{h}h {m}m"
    except Exception:
        return "-"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_POINTS_RE = re.compile(r"\b(\d{2,4})\b")
_NOISE = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Strip whitespace noise for comparison."""
    return _NOISE.sub(" ", text).strip().upper()


def _to_points(text: str) -> int | None:
    """Extract the first 2-4 digit integer from a requirement string."""
    if not text:
        return None
    m = _POINTS_RE.search(text)
    return int(m.group(1)) if m else None
