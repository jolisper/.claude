#!/usr/bin/env python3
"""Apply a confirmed reshape plan: reset, stage, and commit each group in order."""

import sys
import json
import subprocess
import argparse
import os


STAGE_HUNKS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'git-commit', 'scripts', 'stage-hunks.py'
)


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--plan', metavar='PATH')
    parser.add_argument('--help', action='store_true')
    args, unknown = parser.parse_known_args()

    if args.help:
        print("Usage: apply-plan.py --plan PATH")
        print("  Execute a reshape plan: for each group, unstage everything, stage")
        print("  only that group's files/hunks, and commit with its message.")
        print("")
        print("  --plan PATH   path to a JSON file: a list of groups, each with")
        print("                \"message\" (str), and either \"files\" (list of paths)")
        print("                or \"hunks\" (list of {file, hunks: [N,...]})")
        print("")
        print("Example plan.json:")
        print('  [')
        print('    {"message": "refactor: extract helper", "files": ["src/util.py"]},')
        print('    {"message": "feat: add cache", "hunks": [{"file": "src/main.py", "hunks": [1,2]}]}')
        print('  ]')
        print("")
        print("Output: one status=done line per committed group; exits non-zero with an")
        print("        Error on stderr if any group fails (prior groups stay committed).")
        sys.exit(0)

    if unknown:
        print(f"Error: unknown argument: {unknown[0]}", file=sys.stderr)
        print("Try: apply-plan.py --help", file=sys.stderr)
        sys.exit(1)

    if not args.plan:
        print("Error: --plan is required.", file=sys.stderr)
        print("Try: apply-plan.py --help", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.plan) as f:
            groups = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error: cannot read plan {args.plan!r}: {e}", file=sys.stderr)
        print("Try: verify the plan file exists and is valid JSON.", file=sys.stderr)
        sys.exit(1)

    if not isinstance(groups, list) or not groups:
        print("Error: plan must be a non-empty JSON list of groups.", file=sys.stderr)
        sys.exit(1)

    for i, group in enumerate(groups, start=1):
        message = group.get('message')
        if not message:
            print(f"Error: group {i} is missing \"message\".", file=sys.stderr)
            sys.exit(1)

        rc, _, err = run(['git', 'reset'])
        if rc != 0:
            print(f"Error: git reset failed before group {i}: {err.strip()}", file=sys.stderr)
            print(f"Try: inspect working tree state; groups before {i} are already committed.", file=sys.stderr)
            sys.exit(1)

        files = group.get('files', [])
        for path in files:
            rc, _, err = run(['git', 'add', path])
            if rc != 0:
                print(f"Error: git add {path!r} failed in group {i}: {err.strip()}", file=sys.stderr)
                sys.exit(1)

        for hunk_group in group.get('hunks', []):
            path = hunk_group.get('file')
            hunk_numbers = hunk_group.get('hunks', [])
            if not path or not hunk_numbers:
                print(f"Error: group {i} has a hunk entry missing \"file\" or \"hunks\".", file=sys.stderr)
                sys.exit(1)
            hunk_arg = ','.join(str(n) for n in hunk_numbers)
            rc, out, err = run(['python3', STAGE_HUNKS, '--file', path, '--hunks', hunk_arg])
            if rc != 0:
                print(f"Error: stage-hunks.py failed for {path!r} in group {i}: {err.strip()}", file=sys.stderr)
                print(f"Try: inspect working tree state; groups before {i} are already committed.", file=sys.stderr)
                sys.exit(1)

        if not files and not group.get('hunks'):
            print(f"Error: group {i} has no \"files\" or \"hunks\" to stage.", file=sys.stderr)
            sys.exit(1)

        rc, _, err = run(['git', 'commit', '-m', message])
        if rc != 0:
            print(f"Error: git commit failed for group {i}: {err.strip()}", file=sys.stderr)
            print(f"Try: inspect working tree state; groups before {i} are already committed.", file=sys.stderr)
            sys.exit(1)

        print(f"status=done group={i} of {len(groups)}")

    print(f"status=complete groups_committed={len(groups)}")


if __name__ == '__main__':
    main()
