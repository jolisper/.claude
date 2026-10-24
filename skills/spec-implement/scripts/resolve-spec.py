#!/usr/bin/env python3
"""Resolve the spec-implement argument to its spec files.

Usage: resolve-spec.py --arg VALUE [--root DIR]

VALUE is a bare initiative name (resolved to initiatives/<name>/technical-spec.md under
--root, default the current directory) or a path to a technical-spec.md.

Output (key=value): status=ok name= dir= technical= functional=  (functional is empty if absent)
Errors: status=error/message=/hint= on stdout, exit 2.

Example: resolve-spec.py --arg my-feature
"""
import argparse
import os

import speclog as S


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arg", default="")
    p.add_argument("--root", default=".")
    a = p.parse_args()

    arg = a.arg.strip()
    if not arg:
        S.die("spec-implement requires an initiative name or a technical-spec.md path",
              "invoke as /spec-implement <name> or /spec-implement initiatives/<name>/technical-spec.md")
    path = arg if "/" in arg else os.path.join(a.root, "initiatives", arg, "technical-spec.md")
    if not os.path.isfile(path):
        S.die(f"{path} does not exist", "run /spec-technical first, or pass the correct name or path")
    directory = os.path.dirname(os.path.abspath(path))
    functional = os.path.join(directory, "functional-spec.md")
    S.out(name=os.path.basename(directory), dir=directory, technical=os.path.abspath(path),
          functional=functional if os.path.isfile(functional) else "")


if __name__ == "__main__":
    main()
