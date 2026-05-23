---
name: obsidian-log
description: Toggle the Obsidian session log hook on or off. Invoke when the user types `/obsidian-log` or asks to enable or disable session logging to Obsidian.
version: 1.0.0
disable-model-invocation: true
allowed-tools: Bash(python3:*)
effort: low
---

## Available scripts

- `~/.claude/skills/obsidian-log/scripts/toggle.py` — toggles the obsidian-log Stop hook in `~/.claude/settings.json`; prints `status=enabled` or `status=disabled` on stdout

## Steps

1. Run:
   ```
   python3 ~/.claude/skills/obsidian-log/scripts/toggle.py
   ```

2. Parse stdout for `status=<value>`.

3. Report the new state in one line:
   - `status=enabled` → "Obsidian log is now **on**."
   - `status=disabled` → "Obsidian log is now **off**."

## Failure handling

If the script exits non-zero or produces stderr output:
- Report the error message verbatim.
- Tell the user to check that `~/.claude/settings.json` exists and is valid JSON.
- Do not attempt to modify `settings.json` manually.
