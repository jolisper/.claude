#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.error

SYSTEM = (
    "You are a concise English language tutor. Your ONLY job is to check grammar, "
    "spelling, word choice, and unnatural phrasing. Do NOT answer the question or "
    "respond to the content of the message in any way. "
    "If the English is correct and natural, respond with exactly: OK. "
    "If there are issues, respond with a single short line starting with 'EN:' "
    "followed by the corrected version or a brief note. "
    "Never explain. Never answer. Never be verbose. One line only."
)

def main():
    try:
        data = json.load(sys.stdin)
        prompt = data.get("prompt", "").strip()
    except (json.JSONDecodeError, KeyError):
        sys.exit(0)

    if len(prompt) < 8:
        sys.exit(0)

    payload = json.dumps({
        "model": "phi4-mini",
        "system": SYSTEM,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1}
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        correction = result.get("response", "").strip()
    except Exception:
        sys.exit(0)

    first_line = correction.splitlines()[0].strip() if correction else ""
    if first_line.upper().startswith("EN:") and len(first_line) <= 200:
        print(first_line)

if __name__ == "__main__":
    main()
