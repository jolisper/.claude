"""Shared logbook.md handling for the spec-* skills.

Not a CLI. Imported by log.py and stall.py so every reader and writer treats the
frontmatter and the cycle lines the same way. Other spec-* skills that touch
logbook.md should import this module instead of re-implementing the parsing.
"""
import os
import re
import sys

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
CYCLE = re.compile(r"^- cycle (\d+)\.(\d+)(?: \[covered=(\d+)\])?: (.*)$", re.M)


def die(msg, hint):
    print("status=error")
    print(f"message={msg}")
    print(f"hint={hint}")
    sys.exit(2)


def out(**kv):
    print("status=ok")
    for k, v in kv.items():
        print(f"{k}={v}")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        die(f"cannot read {path}: {e.strerror}", "check the path; the log is initiatives/<name>/logbook.md")


def write(path, text):
    tmp = f"{path}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except OSError as e:
        die(f"cannot write {path}: {e.strerror}", "check permissions on the initiative directory")


def text_arg(value):
    """A free-text argument; '-' means read it from stdin (use a heredoc for long or quoted text)."""
    return sys.stdin.read().strip() if value == "-" else value.strip()


def split(text):
    """(frontmatter lines, body). Frontmatter lines are kept raw so unknown keys survive edits."""
    m = FRONTMATTER.match(text)
    if not m:
        return [], text
    return m.group(1).splitlines(), text[m.end():]


def join(lines, body):
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def get(lines, key):
    for line in lines:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def put(lines, key, value):
    new = f"{key}: {value}"
    for i, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[i] = new
            return
    lines.append(new)


def kind(lines):
    """'none' (no frontmatter), 'stub' (spec-initiative log) or 'session' (has last-completed-phase)."""
    if not lines:
        return "none"
    return "session" if get(lines, "last-completed-phase") is not None else "stub"


def cycles(body, phase):
    """[(cycle number, covered or None)] for one phase, in log order."""
    return [(int(m.group(2)), None if m.group(3) is None else int(m.group(3)))
            for m in CYCLE.finditer(body) if int(m.group(1)) == phase]
