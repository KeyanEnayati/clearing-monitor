"""
inject_change.py – manually write a fake entry-requirement change into the
saved state file so the very next poll detects it and writes it to Excel.

Use this to verify the change-detection pipeline without waiting for a real
site to update.

Usage:
    python inject_change.py COINGECKO "Bitcoin" "99999"
    python inject_change.py UCAS_TEST "Accounting and Finance – Aston University" "50"

The next poll will see:  old=<whatever was scraped> → new=<the injected value>
and write that change to Excel with the exact detection timestamp.
"""

import sys
import json
from pathlib import Path

import config as cfg
from state_manager import load_state, save_state


def inject(uni_key: str, course_name: str, fake_req: str):
    state = load_state(cfg.DATA_DIR, uni_key)

    if not state:
        print(f"ERROR: No state found for '{uni_key}'. Run the monitor once first to build a baseline.")
        sys.exit(1)

    # Find a close match if exact name not found
    exact = next((k for k in state if k == course_name), None)
    if exact is None:
        matches = [k for k in state if course_name.lower() in k.lower()]
        if not matches:
            print(f"Course '{course_name}' not found in state for {uni_key}.")
            print("Available courses (first 20):")
            for k in list(state.keys())[:20]:
                print(f"  {k}")
            sys.exit(1)
        if len(matches) > 1:
            print("Multiple matches – be more specific:")
            for m in matches:
                print(f"  {m}")
            sys.exit(1)
        exact = matches[0]

    old_req = state[exact]["req"]
    state[exact]["req"] = fake_req
    save_state(cfg.DATA_DIR, uni_key, state)

    print(f"Injected fake change for '{uni_key}':")
    print(f"  Course : {exact}")
    print(f"  Old req: {old_req}  ->  New (fake): {fake_req}")
    print()
    print("Run the monitor now (or wait for the next poll) to see this recorded in Excel.")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python inject_change.py <UNI_KEY> <COURSE_NAME> <FAKE_REQ>")
        print("Example: python inject_change.py COINGECKO Bitcoin 99999")
        sys.exit(1)

    inject(sys.argv[1], sys.argv[2], sys.argv[3])
