#!/usr/bin/env python3
"""Detect the base branch a given branch was created from."""

import sys
import re
import subprocess
import argparse

PREFERRED_FALLBACKS = ['main', 'master', 'develop', 'dev']


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def detect_from_reflog(branch):
    rc, out, _ = run(['git', 'log', '-g', '--format=%gs', branch])
    if rc != 0:
        return None
    for line in out.splitlines():
        m = re.match(r'branch: Created from (\S+)', line)
        if m:
            return m.group(1)
    return None


def detect_from_branch_list():
    rc, out, _ = run(['git', 'branch', '-a'])
    if rc != 0:
        return None
    names = set()
    for line in out.splitlines():
        name = line.strip().lstrip('* ').split(' ')[0]
        name = name.replace('remotes/origin/', '')
        names.add(name)
    for candidate in PREFERRED_FALLBACKS:
        if candidate in names:
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--branch', metavar='NAME')
    parser.add_argument('--help', action='store_true')
    args, unknown = parser.parse_known_args()

    if args.help:
        print("Usage: detect-base.py --branch NAME")
        print("  Detect the branch NAME was created from: first via reflog")
        print("  (\"branch: Created from <source>\"), then via a preference")
        print("  cascade over local/remote branches (main, master, develop, dev).")
        print("")
        print("  --branch NAME   the branch to detect the base for")
        print("")
        print("Output: status=found base=<name>, or status=ambiguous if neither")
        print("        detection method found a candidate.")
        sys.exit(0)

    if unknown:
        print(f"Error: unknown argument: {unknown[0]}", file=sys.stderr)
        print("Try: detect-base.py --help", file=sys.stderr)
        sys.exit(1)

    if not args.branch:
        print("Error: --branch is required.", file=sys.stderr)
        print("Try: detect-base.py --help", file=sys.stderr)
        sys.exit(1)

    base = detect_from_reflog(args.branch)
    if base:
        print(f"status=found base={base} method=reflog")
        return

    base = detect_from_branch_list()
    if base:
        print(f"status=found base={base} method=fallback")
        return

    print("status=ambiguous")
    print("No reflog match and none of main/master/develop/dev exist.", file=sys.stderr)
    print("Try: ask the user which branch is the base.", file=sys.stderr)


if __name__ == '__main__':
    main()
