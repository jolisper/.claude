# English Tutor Hook — Claude Subprocess Upgrade

**Date:** 2026-05-19
**Status:** Draft v1
**Replaces:** `~/.claude/scripts/english-tutor.py` (Ollama/gemma3:4b implementation)

---

## Problem with the Current Implementation

The current hook calls a local Ollama model (`gemma3:4b`) via HTTP. This has two
drawbacks:

- Ollama must be running for the hook to work — if it isn't, the hook silently exits.
- `gemma3:4b` is a small model; correction quality is inconsistent.

## Proposed Improvement

Replace the Ollama call with a **subprocess invocation of the Claude CLI**. The hook
spawns a completely isolated `claude` process — separate context window, no relation
to the main session agent — passes it the user's prompt, and reads back the correction.

The main session agent is never aware of the subprocess. The correction is injected
via `additionalContext` in the hook's JSON output, exactly as today.

---

## Architecture

```
UserPromptSubmit hook fires
        │
        ▼
english-tutor.py reads prompt from stdin JSON
        │
        ├─ too short / non-English? → exit 0 (no output)
        │
        ▼
spawn: claude --print --model haiku ... "<system prompt>\n\n<user prompt>"
        │
        ▼
parse response: "OK" → exit 0 / "EN: ..." → inject as additionalContext
        │
        ▼
main session sees EN: correction prepended to its context
```

The subprocess is **synchronous** — the hook waits for it before returning. This keeps
the existing behavior: the correction is available before the main session processes
the prompt.

---

## Model Choice

Use `claude-haiku-4-5-20251001` — the fastest and cheapest Claude model. Latency
is the primary concern here since the hook blocks the user's turn.

---

## System Prompt

Same logic as today — flag mode:

```
You are a concise English writing coach for non-native speakers. Your job is to
rewrite the text as a native English speaker would naturally say it — fixing grammar,
spelling, word choice, and unnatural phrasing.

Rules:
1. If the text is not in English, respond with exactly: OK
2. Preserve the original meaning and intent.
3. Do NOT answer the question or respond to the content.
4. If the text already sounds like natural native English, respond with exactly: OK
5. Otherwise, respond with a single short line starting with "EN:" followed by
   the natural native version.
6. Never explain. Never answer. Never be verbose. One line only.
```

---

## Hook Script Changes

The Python script (`~/.claude/scripts/english-tutor.py`) changes only in the
model call section — everything else (language detection, length guard, output
formatting) stays identical.

**Replace:**
```python
payload = json.dumps({...ollama payload...})
req = urllib.request.Request("http://localhost:11434/api/generate", ...)
result = json.loads(resp.read())
correction = result.get("response", "").strip()
```

**With:**
```python
import subprocess
result = subprocess.run(
    ["claude", "--print", "--model", "claude-haiku-4-5-20251001",
     "--system", SYSTEM_FLAG, prompt],
    capture_output=True, text=True, timeout=15
)
correction = result.stdout.strip()
```

---

## Failure Contract

- Claude CLI not found or times out → exit 0 (hook skips silently, session continues).
- Claude returns unexpected output → exit 0.
- Non-zero exit from subprocess → exit 0.

Never block the user's turn due to a tutor failure.

---

## Open Questions

1. **`--print` flag availability** — verify that `claude --print` is the correct
   flag for non-interactive single-turn output in the installed CLI version.
2. **API key in hook context** — confirm that the hook shell environment inherits
   `ANTHROPIC_API_KEY` so the subprocess can authenticate without extra config.
3. **Latency budget** — measure round-trip time for a Haiku call to confirm it's
   acceptable as a blocking hook. If too slow, consider `async: true` and dropping
   the correction into the *next* turn instead.
