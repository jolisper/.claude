#!/usr/bin/env python3
"""PreToolUse hook for spec-implement: warns when the orchestrator writes anything but the logbook.

Usage: guard.py            (reads the hook JSON from stdin; --help prints this text)

Warns, for the orchestrator's own calls (never blocks: the call is always allowed):
  - Write/Edit to any file other than initiatives/<name>/logbook.md
  - Bash commands that write files (redirects, tee, sed -i, heredocs, cp, mv, rm, touch, mkdir)
Allows commands that start with `python3 ~/.claude/skills/spec-implement/scripts/` (the
skill's own scripts, which own all log writes). Sub-agent calls (payload has agent_id) are
always allowed: they are the ones that write code.

The hook stays registered for the whole session, so it goes silent once the implementation
is closed: the project has implementation logs (logbooks with last-completed-phase) and all
of them are `status: complete`. Before `log.py init` creates one, it still warns.

Set SPEC_IMPLEMENT_GUARD=off to disable. A warning is a JSON `additionalContext` (read by
the model) plus `systemMessage` (shown to the user) on stdout, exit 0, with the call
allowed. If the payload cannot be parsed the guard fails open and says so on stderr.
"""
import glob
import json
import os
import re
import sys

LOGBOOK = re.compile(r"(^|/)initiatives/[^/]+/logbook\.md$")
SCRIPTS = ("python3 ~/.claude/skills/spec-implement/scripts/",
           "python3 " + os.path.expanduser("~/.claude/skills/spec-implement/scripts/"))
QUOTED = re.compile(r"\"(?:\\.|[^\"\\])*\"|'[^']*'", re.S)
CHAIN = re.compile(r"&&|\|\||;|\||`|\$\(")
WRITE = re.compile(r"(?<![>&=-])>>?(?![&>])\s*(?!/dev/null)\S|\btee\b|\bsed\s+(-\w*i|--in-place)|<<"
                   r"|(?:^|[\s;&|])(?:cp|mv|rm|touch|mkdir)\s")


def frontmatter(path):
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    keys = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            keys[key.strip()] = value.strip()
    return keys


def implementation_closed(cwd):
    """True when the project has implementation logs and every one is complete."""
    root = os.path.abspath(cwd or os.getcwd())
    while not os.path.isdir(os.path.join(root, "initiatives")):
        parent = os.path.dirname(root)
        if parent == root:
            return False
        root = parent
    logs = [frontmatter(p) for p in glob.glob(os.path.join(root, "initiatives", "*", "logbook.md"))]
    sessions = [fm for fm in logs if "last-completed-phase" in fm]
    return bool(sessions) and all(fm.get("status") == "complete" for fm in sessions)


def warn(reason):
    note = (f"spec-implement: {reason} The orchestrator is meant to delegate writes to "
            "sub-agents through the Agent tool; only initiatives/<name>/logbook.md is expected "
            "from it. The call was allowed.")
    print(json.dumps({"systemMessage": note, "hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "allow",
        "additionalContext": note}}))
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
    if data.get("agent_id") or implementation_closed(data.get("cwd")):
        return
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    if tool in ("Write", "Edit"):
        if not LOGBOOK.search(inp.get("file_path", "")):
            warn(f"the orchestrator is writing {inp.get('file_path')}.")
    elif tool == "Bash":
        cmd = inp.get("command", "")
        # quoted text (log.py --summary "a; b") must not count as shell syntax
        first = QUOTED.sub('""', cmd.lstrip()).split("\n", 1)[0]
        if first.startswith(SCRIPTS) and not CHAIN.search(first):
            return
        if WRITE.search(cmd):
            warn("the orchestrator is writing files through Bash.")


if __name__ == "__main__":
    main()
