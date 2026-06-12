#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import datetime
from typing import Optional

LOG_FILE = "/tmp/english-tutor-debug.log"
CONFIG_FILE = os.path.expanduser("~/.claude/english-tutor.json")

def _log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

def _load_config() -> dict:
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

CLAUDE_BIN = "/opt/homebrew/bin/claude"

SYSTEM_FLAG = (
    "You are a concise English writing coach for non-native speakers. Your job is to "
    "rewrite the text as a native English speaker would naturally say it — fixing grammar, "
    "spelling, word choice, and unnatural phrasing. "
    "Rules: "
    "1. If the text is not in English, respond with exactly: OK. "
    "2. Preserve the original meaning and intent. "
    "3. Do NOT answer the question or respond to the content. "
    "4. Only respond with exactly: OK if the text is already phrased exactly as a native "
    "speaker would say it — no grammar issues, no awkward wording, no better idiomatic "
    "alternative. If there is a more natural, fluent, or idiomatic way to say it, provide "
    "the correction even if the original is grammatically correct. "
    "5. Otherwise, start your response with 'EN:' followed by the full corrected version. "
    "Match the length of the original: a single sentence stays one line; multiple sentences "
    "may span multiple lines. "
    "6. Never add explanations, commentary, or anything beyond the corrected text. "
    "No text before 'EN:', nothing after the last corrected sentence."
)

def call_model(prompt: str) -> str:
    try:
        result = subprocess.run(
            [CLAUDE_BIN, "--print", "--model", "claude-haiku-4-5-20251001", "--system-prompt", SYSTEM_FLAG],
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


def pending_file(session_id: str) -> str:
    return f"/tmp/en_tutor_strict_{session_id}.txt"

def get_pending(session_id: str) -> Optional[str]:
    path = pending_file(session_id)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None

def set_pending(session_id: str, correction: str):
    with open(pending_file(session_id), "w") as f:
        f.write(correction)

def clear_pending(session_id: str):
    path = pending_file(session_id)
    if os.path.exists(path):
        os.remove(path)

def block_with_correction(correction: str, attempt: int = 1):
    label = "Correct your English before continuing" if attempt == 1 else "Still not quite right — try again"
    sys.stderr.write(f"[EN Strict] {label}:\n\n  {correction}\n\nRetype your message using the corrected phrasing.\n")
    sys.exit(2)


def main():
    if os.environ.get("ENGLISH_TUTOR_RUNNING"):
        sys.exit(0)

    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "").strip()
        session_id = data.get("session_id", "default")
    except (json.JSONDecodeError, KeyError):
        sys.exit(0)

    _log(f"PROMPT: {prompt!r}")

    # Bypass: slash commands and very short messages skip the tutor entirely
    if len(prompt) < 8 or prompt.startswith("/"):
        _log("SKIP: too short or slash command")
        clear_pending(session_id)
        sys.exit(0)

    strict = _load_config().get("strict", False)
    pending = get_pending(session_id) if strict else None

    correction = call_model(prompt)
    if not correction:
        if pending:
            clear_pending(session_id)
        sys.exit(0)

    _log(f"MODEL: {correction!r}")
    lines = correction.splitlines()
    first_line = lines[0].strip() if lines else ""

    has_correction = first_line.lstrip(">").lstrip().upper().startswith("EN:")

    if not has_correction:
        _log(f"OK: no EN: prefix ({first_line!r})")
        if pending:
            _log("STRICT: cleared pending — message approved")
            clear_pending(session_id)
        sys.exit(0)

    # Collect full EN: block (drop trailing model chatter after blank line)
    block = []
    for line in lines:
        if not line.strip():
            break
        block.append(line.lstrip(">").lstrip())
    en_block = "\n".join(block)

    corrected_text = first_line.lstrip(">").lstrip()[3:].strip()
    if corrected_text.lower() == prompt.lower():
        _log("SKIP: echo (corrected == prompt)")
        if pending:
            clear_pending(session_id)
        sys.exit(0)

    _log(f"OUTPUT: {en_block!r}")

    if not strict:
        # Normal mode: inject correction as context and let the agent display it
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": en_block
            }
        }))
        return

    # Strict mode: block and demand a corrected retry
    set_pending(session_id, corrected_text)
    attempt = 2 if pending else 1
    _log(f"STRICT: blocking (attempt {attempt}), correction={corrected_text!r}")
    block_with_correction(corrected_text, attempt)


if __name__ == "__main__":
    main()
