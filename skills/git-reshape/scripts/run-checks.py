#!/usr/bin/env python3
"""Detect and run the project's build/test command."""

import sys
import os
import subprocess
import argparse
import json


def detect_command(root):
    pkg = os.path.join(root, 'package.json')
    if os.path.isfile(pkg):
        try:
            with open(pkg) as f:
                data = json.load(f)
            scripts = data.get('scripts', {})
            if 'test' in scripts:
                return ['npm', 'test', '--silent']
        except (OSError, json.JSONDecodeError):
            pass

    if os.path.isfile(os.path.join(root, 'Cargo.toml')):
        return ['cargo', 'test']

    if os.path.isfile(os.path.join(root, 'pyproject.toml')) or os.path.isfile(os.path.join(root, 'setup.py')):
        return ['pytest']

    if os.path.isfile(os.path.join(root, 'Makefile')):
        return ['make', 'test']

    return None


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--root', metavar='PATH', default='.')
    parser.add_argument('--help', action='store_true')
    args, unknown = parser.parse_known_args()

    if args.help:
        print("Usage: run-checks.py [--root PATH]")
        print("  Detect the project's build/test command (package.json, Cargo.toml,")
        print("  pyproject.toml/setup.py, Makefile) and run it.")
        print("")
        print("  --root PATH   project root to inspect (default: current directory)")
        print("")
        print("Output: status=pass or status=fail, followed by the command's output.")
        print("        status=none if no recognized project type was found.")
        sys.exit(0)

    if unknown:
        print(f"Error: unknown argument: {unknown[0]}", file=sys.stderr)
        print("Try: run-checks.py --help", file=sys.stderr)
        sys.exit(1)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"Error: --root {args.root!r} is not a directory.", file=sys.stderr)
        sys.exit(1)

    command = detect_command(root)
    if command is None:
        print("status=none")
        print("No recognized project type (package.json, Cargo.toml, pyproject.toml, setup.py, Makefile) found.")
        sys.exit(0)

    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode == 0:
        print(f"status=pass command={' '.join(command)}")
    else:
        print(f"status=fail command={' '.join(command)} exit_code={result.returncode}")
        sys.exit(1)


if __name__ == '__main__':
    main()
