#!/usr/bin/env python3
import json
import sys
import urllib.request
import datetime

LOG_FILE = "/tmp/english-tutor-debug.log"

def _log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

# "rewrite" mode: model always returns corrected text; we compare to detect changes.
# "flag" mode: model returns "OK" or "EN: correction".
MODEL = "gemma3:4b"
MODE = "flag"

SYSTEM_FLAG = (
    "You are a concise English grammar checker. Your ONLY job is to fix grammar, "
    "spelling, and word choice errors in English text. "
    "Rules: "
    "1. If the text is not in English, respond with exactly: OK. "
    "2. Do NOT rephrase, rewrite, or change the meaning. "
    "3. Do NOT answer the question or respond to the content. "
    "4. Only fix actual errors — if the English is correct, respond with exactly: OK. "
    "5. If there are errors, respond with a single short line starting with 'EN:' "
    "followed by the minimally corrected version. "
    "6. Never explain. Never answer. Never be verbose. One line only."
)

def _is_english(text: str) -> bool:
    try:
        from langdetect import detect
        return detect(text) == "en"
    except Exception:
        return True  # fail open: if detection fails, let the model handle it


def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "").strip()
    except (json.JSONDecodeError, KeyError):
        sys.exit(0)

    _log(f"PROMPT: {prompt!r}")

    if len(prompt) < 8:
        _log("SKIP: too short")
        sys.exit(0)

    if not _is_english(prompt):
        _log("SKIP: non-english")
        sys.exit(0)

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    } | ({"system": SYSTEM_FLAG} if MODE == "flag" else {})).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        correction = result.get("response", "").strip()
    except Exception as e:
        _log(f"ERROR: {e}")
        sys.exit(0)

    _log(f"MODEL: {correction!r}")
    first_line = correction.splitlines()[0].strip() if correction else ""

    if MODE == "rewrite":
        if not first_line or first_line.lower() == prompt.lower() or len(first_line) > 200:
            _log("SKIP: rewrite unchanged or too long")
            sys.exit(0)
        en_line = f"EN: {first_line}"
    else:
        if not first_line.upper().startswith("EN:") or len(first_line) > 200:
            _log(f"SKIP: no EN: prefix or too long ({first_line!r})")
            sys.exit(0)
        corrected_text = first_line[3:].strip()
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
