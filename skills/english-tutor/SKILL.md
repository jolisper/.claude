---
name: english-tutor
description: Toggle the English tutor hook on or off, or enable/disable strict mode. Invoke when the user types `/english-tutor` or asks to enable/disable English corrections or strict mode.
version: 1.1.0
disable-model-invocation: true
allowed-tools: Bash(python3:*)
effort: low
---

## Available scripts

- `~/.claude/skills/english-tutor/scripts/toggle.py` — manages the English tutor hook and its config

## Steps

### Toggle hook on/off (no args)

```
python3 ~/.claude/skills/english-tutor/scripts/toggle.py
```

Parse stdout for `status=<value>`:
- `status=enabled`  → "English tutor is now **on**."
- `status=disabled` → "English tutor is now **off**."

### Toggle strict mode

```
python3 ~/.claude/skills/english-tutor/scripts/toggle.py strict on
python3 ~/.claude/skills/english-tutor/scripts/toggle.py strict off
```

Parse stdout for `strict=<value>`:
- `strict=on`  → "Strict mode is now **on**. Messages with English errors will be blocked until corrected."
- `strict=off` → "Strict mode is now **off**. English corrections will be shown as hints only."

## Failure handling

If the script exits non-zero or produces stderr output:
- Report the error message verbatim.
- Tell the user to check that `~/.claude/settings.json` and `~/.claude/english-tutor.json` exist and are valid JSON.
- Do not attempt to modify those files manually.
