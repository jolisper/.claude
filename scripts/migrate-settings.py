#!/usr/bin/env python3
"""Moves non-whitelisted keys from settings.json to settings.local.json."""
import json, os, sys
from pathlib import Path

SETTINGS = "settings.json"
LOCAL = "settings.local.json"
WHITELIST_FILE = Path(__file__).parent / "settings-whitelist.txt"

tracked_keys = set(WHITELIST_FILE.read_text().split())

with open(SETTINGS) as f:
    settings = json.load(f)

keys_to_move = {k: v for k, v in settings.items() if k not in tracked_keys}
if not keys_to_move:
    print("Nothing to migrate.")
    sys.exit(0)

for k in keys_to_move:
    del settings[k]

local = {}
if os.path.exists(LOCAL):
    with open(LOCAL) as f:
        local = json.load(f)
local.update(keys_to_move)

with open(SETTINGS, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

with open(LOCAL, "w") as f:
    json.dump(local, f, indent=2)
    f.write("\n")

print(f"Migrated {list(keys_to_move)} → {LOCAL}")
