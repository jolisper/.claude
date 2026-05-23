#!/usr/bin/env python3
import json, sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "bash ~/.claude/skills/obsidian-log/scripts/stop-hook.sh"
HOOK_ENTRY = {"hooks": [{"type": "command", "command": HOOK_COMMAND}]}

def main():
    if not SETTINGS_PATH.exists():
        print(f"error: {SETTINGS_PATH} not found", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(SETTINGS_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    hooks = data.setdefault("hooks", {})
    stop_hooks = hooks.setdefault("Stop", [])

    hook_idx = None
    for i, group in enumerate(stop_hooks):
        for hook in group.get("hooks", []):
            if hook.get("command") == HOOK_COMMAND:
                hook_idx = i
                break

    if hook_idx is not None:
        stop_hooks.pop(hook_idx)
        new_state = "disabled"
    else:
        stop_hooks.append(HOOK_ENTRY)
        new_state = "enabled"

    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"status={new_state}")

if __name__ == "__main__":
    main()
