#!/usr/bin/env python3
"""PreToolUse hook for spec-implement: the orchestrator may only write the logbook.

Usage: guard.py            (reads the hook JSON from stdin; --help prints this text)

Denies, for the orchestrator's own calls:
  - Write/Edit to any file other than initiatives/<name>/logbook.md
  - Bash commands that write files (redirects, tee, sed -i, heredocs, cp, mv, rm, touch, mkdir)
Allows commands that start with `python3 ~/.claude/skills/spec-implement/scripts/` (the
skill's own scripts, which own all log writes). Sub-agent calls (payload has agent_id) are
always allowed: they are the ones that write code.

Set SPEC_IMPLEMENT_GUARD=off to disable. A denial is a JSON permissionDecision on stdout,
exit 0. If the payload cannot be parsed the guard fails open and says so on stderr.
"""
import json
import os
import re
import sys

LOGBOOK = re.compile(r"(^|/)initiatives/[^/]+/logbook\.md$")
SCRIPTS = ("python3 ~/.claude/skills/spec-implement/scripts/",
           "python3 " + os.path.expanduser("~/.claude/skills/spec-implement/scripts/"))
CHAIN = re.compile(r"&&|\|\||;|\||`|\$\(")
WRITE = re.compile(r"(?<![>&=-])>>?(?![&>])\s*(?!/dev/null)\S|\btee\b|\bsed\s+(-\w*i|--in-place)|<<"
                   r"|(?:^|[\s;&|])(?:cp|mv|rm|touch|mkdir)\s")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": f"spec-implement: {reason} All code goes through the Agent tool."}}))
    sys.exit(0)


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    if os.environ.get("SPEC_IMPLEMENT_GUARD") == "off":
        return
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"guard.py: unparseable hook input ({e}); allowing", file=sys.stderr)
        return
    if data.get("agent_id"):
        return
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    if tool in ("Write", "Edit"):
        if not LOGBOOK.search(inp.get("file_path", "")):
            deny(f"the orchestrator may only write initiatives/<name>/logbook.md, not {inp.get('file_path')}.")
    elif tool == "Bash":
        cmd = inp.get("command", "")
        first = cmd.lstrip().split("\n", 1)[0]
        if first.startswith(SCRIPTS) and not CHAIN.search(first):
            return
        if WRITE.search(cmd):
            deny("the orchestrator may not write files through Bash.")


if __name__ == "__main__":
    main()
