#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import datetime

LOG_FILE = "/tmp/english-tutor-debug.log"

def _log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

CLAUDE_BIN = "/opt/homebrew/bin/claude"

SYSTEM_FLAG = (
    "You are a concise English writing coach for non-native speakers. Your job is to "
    "rewrite the text as a native English speaker would naturally say it — fixing grammar, "
    "spelling, word choice, and unnatural phrasing. "
    "Rules: "
    "1. If the text is not in English, respond with exactly: OK. "
    "2. Preserve the original meaning and intent. "
    "3. Do NOT answer the question or respond to the content. "
    "4. If the text already sounds like natural native English, respond with exactly: OK. "
    "5. Otherwise, respond with a single short line starting with 'EN:' "
    "followed by the natural native version. "
    "6. Never explain. Never answer. Never be verbose. One line only."
)

def call_model(prompt: str) -> str:
    try:
        result = subprocess.run(
            [CLAUDE_BIN, "--print", "--system-prompt", SYSTEM_FLAG],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "ENGLISH_TUTOR_RUNNING": "1"},
        )
        return result.stdout.strip()
    except Exception as e:
        _log(f"CALL_MODEL_ERROR: {type(e).__name__}: {e}")
        return ""


def main():
    if os.environ.get("ENGLISH_TUTOR_RUNNING"):
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "").strip()
    except (json.JSONDecodeError, KeyError):
        sys.exit(0)

    _log(f"PROMPT: {prompt!r}")

    if len(prompt) < 8:
        _log("SKIP: too short")
        sys.exit(0)

    correction = call_model(prompt)
    if not correction:
        sys.exit(0)

    _log(f"MODEL: {correction!r}")
    first_line = correction.splitlines()[0].strip() if correction else ""

    if not first_line.lstrip(">").upper().startswith("EN:") or len(first_line) > 200:
        _log(f"SKIP: no EN: prefix or too long ({first_line!r})")
        sys.exit(0)
    corrected_text = first_line.lstrip(">").lstrip()[3:].strip()
    if corrected_text.lower() == prompt.lower():
        _log("SKIP: echo (corrected == prompt)")
        sys.exit(0)
    en_line = first_line

    _log(f"OUTPUT: {en_line!r}")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": en_line
        }
    }))

if __name__ == "__main__":
    main()
