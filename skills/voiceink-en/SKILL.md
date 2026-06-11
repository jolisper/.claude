---
name: voiceink-en
description: Switch VoiceInk's transcription language to English. Invoke when the user types /voiceink-en or asks to switch VoiceInk to English.
version: 1.0.0
disable-model-invocation: true
allowed-tools: Bash(bash:*)
effort: low
---

## Available scripts

- `~/.claude/skills/voiceink-en/scripts/set-en.sh` — kills VoiceInk, sets `SelectedLanguage` to `en`, restarts it in the background, and returns focus to the previously active app; prints `status=done lang=en` and a human-readable result line on stdout.

## Abort conditions

Stop before running the script if:
- VoiceInk is not running (`pgrep -x VoiceInk` returns non-zero) — report: "VoiceInk is not running — start it first." and stop.

## Steps

1. Check VoiceInk is running:
   ```
   pgrep -x VoiceInk
   ```
   If not running, stop (see Abort conditions).

2. Run:
   ```
   bash ~/.claude/skills/voiceink-en/scripts/set-en.sh
   ```

3. Parse stdout for `status=done`:
   - `status=done` → print the summary line to the user (`VoiceInk → 🇺🇸 English`)
   - Non-zero exit or no `status=done` → report the error verbatim and stop

## Failure handling

If the script fails, report the error and show the manual recovery commands:

```
pkill -x VoiceInk
sleep 3
defaults write com.prakashjoshipax.VoiceInk SelectedLanguage en
open -g /Applications/VoiceInk.app
```
