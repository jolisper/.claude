#!/usr/bin/env python3
"""Maintain initiatives/<name>/logbook.md for spec-implement.

Usage: log.py <command> [flags]      (free-text flags accept '-' to read stdin)

  status      --log PATH
  init        --spec PATH --feature NAME --intro TEXT --plan TEXT [--overwrite]
  resume      --log PATH --from N
  cycle       --log PATH --phase P --n K --behavior TEXT
  cycle-done  --log PATH --phase P --n K --covered C --summary TEXT
  phase-done  --log PATH --phase N --type Scaffold|TDD --name NAME --summary TEXT
  close       --log PATH --summary TEXT --files TEXT

Output is key=value lines on stdout, starting with status=ok|unchanged|error.
Errors go to stdout as status=error/message=/hint= with exit code 2.
Every command is idempotent: repeating it with the same arguments is safe.

Examples:
  log.py init --spec initiatives/x/technical-spec.md --feature X --intro "..." --plan - <<'EOF'
  1. [Scaffold] ...
  EOF
  log.py cycle --log initiatives/x/logbook.md --phase 3 --n 1 --behavior "add(2,3) returns 5"
"""
import argparse
import os
import re
import sys
from datetime import date

import speclog as S


def cmd_status(a):
    lines, _ = S.split(S.read(a.log))
    S.out(kind=S.kind(lines), last_completed=S.get(lines, "last-completed-phase") or "")


def cmd_init(a):
    log = os.path.join(os.path.dirname(os.path.abspath(a.spec)), "logbook.md")
    body = (f"\n# Implementation Log: {a.feature}\n\n{S.text_arg(a.intro)}\n\n"
            f"## Phase Plan\n\n{S.text_arg(a.plan)}\n")
    today = date.today().isoformat()
    spec = a.spec
    if not os.path.exists(log):
        lines = [f"spec: {spec}", f"started: {today}", "last-completed-phase: 0", "status: in-progress"]
        S.write(log, S.join(lines, body))
        S.out(log=log, mode="created")
        return
    lines, old = S.split(S.read(log))
    if S.kind(lines) == "session" and not a.overwrite:
        S.die(f"{log} already holds an implementation log (last-completed-phase: "
              f"{S.get(lines, 'last-completed-phase')})",
              "use 'resume' to continue it, or pass --overwrite to start over")
    if S.kind(lines) == "session":
        fresh = [f"spec: {spec}", f"started: {today}", "last-completed-phase: 0", "status: in-progress"]
        S.write(log, S.join(fresh, body))
        S.out(log=log, mode="overwritten")
        return
    # initiative stub (or no frontmatter): merge, keeping its started/status
    S.put(lines, "spec", spec)
    if S.get(lines, "started") is None:
        S.put(lines, "started", today)
    S.put(lines, "last-completed-phase", 0)
    if S.get(lines, "status") is None:
        S.put(lines, "status", "in-progress")
    S.write(log, S.join(lines, old.rstrip("\n") + "\n" + body))
    S.out(log=log, mode="merged")


def cmd_resume(a):
    text = S.read(a.log)
    divider = f"\n---\nResumed: {date.today().isoformat()}, starting from phase {a.from_phase}\n---\n"
    if text.endswith(divider):
        S.out(status_note="divider already present")
        return
    S.write(a.log, text.rstrip("\n") + "\n" + divider)
    S.out(resume_from=a.from_phase)


def cmd_cycle(a):
    text = S.read(a.log)
    line = f"- cycle {a.phase}.{a.n}: {S.text_arg(a.behavior)}"
    pat = re.compile(rf"^- cycle {a.phase}\.{a.n}\b.*$", re.M)
    if pat.search(text):
        text = pat.sub(lambda _: line, text, count=1)
    else:
        header = f"### Phase {a.phase} cycles"
        if header not in text:
            text = text.rstrip("\n") + f"\n\n{header}\n\n"
        else:
            text = text.rstrip("\n") + "\n"
        text += line + "\n"
    S.write(a.log, text)
    S.out(cycle=f"{a.phase}.{a.n}")


def cmd_cycle_done(a):
    text = S.read(a.log)
    pat = re.compile(rf"^- cycle {a.phase}\.{a.n}(?: \[covered=\d+\])?: (.*?)(?: — .*)?$", re.M)
    m = pat.search(text)
    if not m:
        S.die(f"cycle {a.phase}.{a.n} is not in {a.log}",
              "run 'cycle' for this phase and number before 'cycle-done'")
    line = f"- cycle {a.phase}.{a.n} [covered={a.covered}]: {m.group(1)} — {S.text_arg(a.summary)}"
    S.write(a.log, text[:m.start()] + line + text[m.end():])
    S.out(cycle=f"{a.phase}.{a.n}", covered=a.covered)


def cmd_phase_done(a):
    text = S.read(a.log)
    header = f"## Phase {a.phase} — [{a.type}] {a.name}"
    if header in text:
        print("status=unchanged")
        print(f"message=phase {a.phase} already recorded")
        return
    lines, body = S.split(text)
    if not lines:
        S.die(f"{a.log} has no frontmatter", "run 'init' first")
    S.put(lines, "last-completed-phase", a.phase)
    S.write(a.log, S.join(lines, body.rstrip("\n") + f"\n\n{header}\n\n{S.text_arg(a.summary)}\n"))
    S.out(last_completed=a.phase)


def cmd_close(a):
    text = S.read(a.log)
    if "## Implementation files" in text:
        print("status=unchanged")
        print("message=log already closed")
        return
    lines, body = S.split(text)
    if not lines:
        S.die(f"{a.log} has no frontmatter", "run 'init' first")
    S.put(lines, "status", "complete")
    files = [f.strip() for f in S.text_arg(a.files).splitlines() if f.strip()]
    section = "\n".join(f"- {f}" for f in files)
    S.write(a.log, S.join(lines, body.rstrip("\n")
                          + f"\n\n{S.text_arg(a.summary)}\n\n## Implementation files\n\n{section}\n"))
    S.out(files=len(files))


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *flags, **typed):
        sp = sub.add_parser(name)
        for f in flags:
            sp.add_argument(f"--{f.replace('_', '-')}", dest=f, required=True, type=typed.get(f, str))
        sp.set_defaults(fn=fn)
        return sp

    add("status", cmd_status, "log")
    add("init", cmd_init, "spec", "feature", "intro", "plan").add_argument("--overwrite", action="store_true")
    add("resume", cmd_resume, "log", "from_phase", from_phase=int)
    add("cycle", cmd_cycle, "log", "phase", "n", "behavior", phase=int, n=int)
    add("cycle-done", cmd_cycle_done, "log", "phase", "n", "covered", "summary", phase=int, n=int, covered=int)
    add("phase-done", cmd_phase_done, "log", "phase", "type", "name", "summary", phase=int)
    add("close", cmd_close, "log", "summary", "files")
    return p


if __name__ == "__main__":
    args = parser().parse_args()
    if getattr(args, "type", None) and args.type not in ("Scaffold", "TDD"):
        S.die(f"--type must be Scaffold or TDD, got {args.type}", "pass --type Scaffold or --type TDD")
    args.fn(args)
