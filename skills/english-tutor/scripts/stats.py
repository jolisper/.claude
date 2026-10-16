#!/usr/bin/env python3
import json, sys
from datetime import date, timedelta
from pathlib import Path

LOG_DIR = Path.home() / ".english-tutor" / "logs"
DEFAULT_DAYS = 30
MAX_PAIRS = 200

def load_entries(days: int) -> list:
    since = date.today() - timedelta(days=days - 1)
    entries = []
    for path in sorted(LOG_DIR.glob("*.jsonl")):
        try:
            if date.fromisoformat(path.stem) < since:
                continue
        except ValueError:
            continue
        for line in path.read_text().splitlines():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries

def main():
    args = sys.argv[1:]
    try:
        days = int(args[0]) if args else DEFAULT_DAYS
    except ValueError:
        print("error: usage: stats.py [days]", file=sys.stderr)
        sys.exit(1)

    entries = load_entries(days)
    checked = len(entries)
    counts = {k: sum(1 for e in entries if e.get("result") == k) for k in ("clean", "error", "style")}
    blocked = sum(1 for e in entries if e.get("action") == "drop")

    print(f"days={days}")
    print(f"checked={checked}")
    for k, v in counts.items():
        print(f"{k}={v}")
    print(f"blocked={blocked}")

    corrections = [e for e in entries if e.get("result") in ("error", "style")][-MAX_PAIRS:]
    print("--- corrections")
    for e in corrections:
        print(json.dumps({"kind": e["result"], "original": e.get("original"), "corrected": e.get("corrected")}))

if __name__ == "__main__":
    main()
