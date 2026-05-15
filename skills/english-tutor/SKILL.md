---
name: english-tutor
description: Toggle the English tutor hook on or off. Invoke when the user types `/english-tutor` or asks to enable or disable English corrections on their messages.
version: 1.0.0
disable-model-invocation: true
allowed-tools: Bash(python3:*)
effort: low
---

## Available scripts

- `~/.claude/skills/english-tutor/scripts/toggle.py` — toggles the english-tutor hook in `~/.claude/settings.json`; prints `status=enabled` or `status=disabled` on stdout

## Steps

1. Run:
   ```
   python3 ~/.claude/skills/english-tutor/scripts/toggle.py
   ```

2. Parse stdout for `status=<value>`.

3. Report the new state in one line:
   - `status=enabled` → "English tutor is now **on**."
   - `status=disabled` → "English tutor is now **off**."

## Failure handling

If the script exits non-zero or produces stderr output:
- Report the error message verbatim.
- Tell the user to check that `~/.claude/settings.json` exists and is valid JSON.
- Do not attempt to modify `settings.json` manually.
