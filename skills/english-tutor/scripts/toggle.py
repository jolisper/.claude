#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
CONFIG_PATH   = Path.home() / ".claude" / "english-tutor.json"
PLUGIN_ID     = "english-tutor@jolisper-mods"

DEFAULT_CONFIG = {"strict": False}

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        return json.loads(CONFIG_PATH.read_text())
    except json.JSONDecodeError:
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")

def toggle_hook():
    load_config()  # ensure config file exists
    if not SETTINGS_PATH.exists():
        print(f"error: {SETTINGS_PATH} not found", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(SETTINGS_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    enabled_plugins = data.get("enabledPlugins", {})
    currently_enabled = enabled_plugins.get(PLUGIN_ID, True)
    action = "disable" if currently_enabled else "enable"

    result = subprocess.run(
        ["claude", "plugin", action, PLUGIN_ID],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    new_state = "disabled" if action == "disable" else "enabled"
    print(f"status={new_state}")

def set_strict(value: bool):
    cfg = load_config()
    cfg["strict"] = value
    save_config(cfg)
    state = "on" if value else "off"
    print(f"strict={state}")

def main():
    args = sys.argv[1:]

    if not args:
        toggle_hook()
        return

    if args[0] == "strict":
        if len(args) < 2 or args[1] not in ("on", "off"):
            print("error: usage: toggle.py strict on|off", file=sys.stderr)
            sys.exit(1)
        set_strict(args[1] == "on")
        return

    print(f"error: unknown subcommand '{args[0]}'", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
