"""
state_manager.py – persists the last-known entry requirement for every course
at every university so we can detect changes between polls.

Storage: data/state/<uni_key>.json
Format:  { "course_name": {"req": "...", "first_seen": "ISO", "last_changed": "ISO"} }
"""

import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)


def _path(data_dir: Path, uni_key: str) -> Path:
    d = data_dir / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{uni_key}.json"


def load_state(data_dir: Path, uni_key: str) -> dict:
    p = _path(data_dir, uni_key)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("Could not load state for %s: %s", uni_key, e)
        return {}


def save_state(data_dir: Path, uni_key: str, state: dict):
    p = _path(data_dir, uni_key)
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def apply_changes(data_dir: Path, uni_key: str, changes: list[dict]) -> dict:
    """Update persisted state with confirmed changes. Returns new state."""
    state = load_state(data_dir, uni_key)
    now   = datetime.now().isoformat(timespec="seconds")
    for ch in changes:
        course = ch["course"]
        if ch["kind"] == "removed":
            state.pop(course, None)
        else:
            state[course] = {
                "req":          ch["new_req"],
                "first_seen":   state.get(course, {}).get("first_seen", now),
                "last_changed": now,
            }
    save_state(data_dir, uni_key, state)
    return state
