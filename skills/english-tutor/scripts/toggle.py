#!/usr/bin/env python3
import json, sys
from pathlib import Path

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/scripts/english-tutor.py"
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
    submit_hooks = hooks.setdefault("UserPromptSubmit", [])

    tutor_idx = None
    for i, group in enumerate(submit_hooks):
        for hook in group.get("hooks", []):
            if hook.get("command") == HOOK_COMMAND:
                tutor_idx = i
                break

    if tutor_idx is not None:
        submit_hooks.pop(tutor_idx)
        new_state = "disabled"
    else:
        submit_hooks.append(HOOK_ENTRY)
        new_state = "enabled"

    SETTINGS_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"status={new_state}")

if __name__ == "__main__":
    main()
