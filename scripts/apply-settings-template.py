#!/usr/bin/env python3
"""Merges settings.template.json into settings.local.json, prompting on conflicts."""
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEMPLATE = REPO_ROOT / "settings.template.json"
LOCAL = REPO_ROOT / "settings.json"

CONFLICT_NOTES = {
    "statusLine": (
        "Without this setting, the status line won't work in this repo."
    ),
}


def format_value(v):
    return json.dumps(v, indent=2)


def prompt_conflict(key, current, template_val):
    note = CONFLICT_NOTES.get(key)
    print(f"\nConflict: '{key}'")
    if note:
        print(f"  ⚠  {note}")
    print(f"  Current:  {format_value(current)}")
    print(f"  Template: {format_value(template_val)}")
    while True:
        choice = input("  [k]eep current  [u]se template  [s]kip: ").strip().lower()
        if choice in ("k", "u", "s"):
            return choice
        print("  Please enter k, u, or s.")


def main():
    if not TEMPLATE.exists():
        print(f"Template not found: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE) as f:
        template = json.load(f)

    local = {}
    if LOCAL.exists():
        with open(LOCAL) as f:
            local = json.load(f)

    changed = False
    for key, template_val in template.items():
        if key not in local:
            local[key] = template_val
            print(f"  Added '{key}'")
            changed = True
        elif local[key] == template_val:
            print(f"  Skipped '{key}' (already matches template)")
        else:
            choice = prompt_conflict(key, local[key], template_val)
            if choice == "u":
                local[key] = template_val
                print(f"  Updated '{key}' with template value")
                changed = True
            elif choice == "k":
                print(f"  Kept current '{key}'")
            else:
                print(f"  Skipped '{key}'")

    if changed:
        with open(LOCAL, "w") as f:
            json.dump(local, f, indent=2)
            f.write("\n")
        print(f"\nWrote {LOCAL}")
    else:
        print("\nNo changes made.")


if __name__ == "__main__":
    main()
