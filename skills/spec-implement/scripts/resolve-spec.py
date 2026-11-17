#!/usr/bin/env python3
"""Resolve the spec-implement argument to its spec files.

Usage: resolve-spec.py --arg "VALUE [--auto]" [--root DIR]

A standalone --auto token in VALUE is a flag (auto-verify mode) and is stripped before resolving.
VALUE is a bare initiative name (resolved to initiatives/<name>/technical-spec.md under
--root, default the current directory) or a path to a technical-spec.md.

Output (key=value): status=ok name= dir= technical= functional=  (functional is empty if absent)
  Also auto=false, or with --auto: auto=true rounds=<speclog.MAX_ROUNDS>
Errors: status=error/message=/hint= on stdout, exit 2.

Example: resolve-spec.py --arg my-feature
"""
import argparse
import os
import sys

import speclog as S


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arg", default="")
    p.add_argument("--root", default=".")
    argv = sys.argv[1:]
    for i, t in enumerate(argv[:-1]):
        if t == "--arg" and argv[i + 1] == "--auto":
            argv[i:i + 2] = ["--arg=--auto"]  # argparse would otherwise reject --auto as the value
            break
    a = p.parse_args(argv)

    tokens = a.arg.split()
    auto = "--auto" in tokens
    arg = " ".join(t for t in tokens if t != "--auto")
    if not arg:
        S.die("spec-implement requires an initiative name or a technical-spec.md path",
              "invoke as /spec-implement <name> or /spec-implement initiatives/<name>/technical-spec.md")
    path = arg if "/" in arg else os.path.join(a.root, "initiatives", arg, "technical-spec.md")
    if not os.path.isfile(path):
        S.die(f"{path} does not exist", "run /spec-technical first, or pass the correct name or path")
    directory = os.path.dirname(os.path.abspath(path))
    functional = os.path.join(directory, "functional-spec.md")
    kv = dict(name=os.path.basename(directory), dir=directory, technical=os.path.abspath(path),
              functional=functional if os.path.isfile(functional) else "")
    if auto:
        kv.update(auto="true", rounds=S.MAX_ROUNDS)
    else:
        kv.update(auto="false")
    S.out(**kv)


if __name__ == "__main__":
    main()
