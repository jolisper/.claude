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
    lines = correction.splitlines()
    first_line = lines[0].strip() if lines else ""

    if not first_line.lstrip(">").lstrip().upper().startswith("EN:"):
        _log(f"SKIP: no EN: prefix ({first_line!r})")
        sys.exit(0)

    # Collect all lines until the first blank line (drops trailing model chatter)
    block = []
    for line in lines:
        if not line.strip():
            break
        block.append(line.lstrip(">").lstrip())
    en_block = "\n".join(block)

    corrected_text = first_line.lstrip(">").lstrip()[3:].strip()
    if corrected_text.lower() == prompt.lower():
        _log("SKIP: echo (corrected == prompt)")
        sys.exit(0)

    _log(f"OUTPUT: {en_block!r}")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": en_block
        }
    }))

if __name__ == "__main__":
    main()
