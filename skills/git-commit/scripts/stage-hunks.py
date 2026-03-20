#!/usr/bin/env python3
"""Stage specific hunks of a file using git apply --cached."""

import sys
import subprocess
import argparse
import tempfile
import os


def get_diff(filepath):
    result = subprocess.run(
        ['git', 'diff', '--', filepath],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: git diff failed: {result.stderr.strip()}", file=sys.stderr)
        print(f"Expected: a valid file path tracked by git.", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def parse_hunks(diff):
    """Split diff into header lines and a list of hunk line-groups."""
    lines = diff.splitlines(keepends=True)
    header = []
    hunks = []
    current_hunk = []
    in_header = True

    for line in lines:
        if line.startswith('@@'):
            in_header = False
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
        elif in_header:
            header.append(line)
        else:
            current_hunk.append(line)

    if current_hunk:
        hunks.append(current_hunk)

    return header, hunks


def apply_patch(patch_content):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(patch_content)
        patch_path = f.name
    try:
        result = subprocess.run(
            ['git', 'apply', '--cached', patch_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Error: git apply --cached failed: {result.stderr.strip()}", file=sys.stderr)
            print("Try: verify the file has unstaged changes and the hunk numbers are correct.", file=sys.stderr)
            sys.exit(1)
    finally:
        os.unlink(patch_path)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--file', metavar='PATH')
    parser.add_argument('--hunks', metavar='N[,N,...]')
    parser.add_argument('--help', action='store_true')
    args, unknown = parser.parse_known_args()

    if args.help:
        print("Usage: stage-hunks.py --file PATH --hunks N[,N,...]")
        print("  Stage specific hunks of a file without staging the whole file.")
        print("")
        print("  --file PATH       path to the file (relative to repo root)")
        print("  --hunks N[,N...]  comma-separated hunk numbers to stage (1-based)")
        print("")
        print("Example: stage-hunks.py --file src/foo.py --hunks 1,3")
        print("Output:  status=done file=<path> hunks_staged=<N>")
        sys.exit(0)

    if unknown:
        print(f"Error: unknown argument: {unknown[0]}", file=sys.stderr)
        print("Try: stage-hunks.py --help", file=sys.stderr)
        sys.exit(1)

    if not args.file:
        print("Error: --file is required.", file=sys.stderr)
        print("Try: stage-hunks.py --help", file=sys.stderr)
        sys.exit(1)

    if not args.hunks:
        print("Error: --hunks is required.", file=sys.stderr)
        print("Try: stage-hunks.py --help", file=sys.stderr)
        sys.exit(1)

    try:
        hunk_numbers = [int(n.strip()) for n in args.hunks.split(',')]
    except ValueError:
        print(f"Error: --hunks must be comma-separated integers, got: {args.hunks!r}", file=sys.stderr)
        sys.exit(1)

    diff = get_diff(args.file)
    if not diff:
        print(f"Error: no unstaged changes found in {args.file!r}.", file=sys.stderr)
        sys.exit(1)

    header, hunks = parse_hunks(diff)
    if not hunks:
        print(f"Error: no hunks found in diff for {args.file!r}.", file=sys.stderr)
        sys.exit(1)

    invalid = [n for n in hunk_numbers if n < 1 or n > len(hunks)]
    if invalid:
        print(f"Error: hunk number(s) out of range: {invalid}. {args.file!r} has {len(hunks)} hunk(s).", file=sys.stderr)
        sys.exit(1)

    selected = [hunks[n - 1] for n in hunk_numbers]
    patch = ''.join(header) + ''.join(''.join(h) for h in selected)

    apply_patch(patch)

    print(f"status=done file={args.file} hunks_staged={len(selected)}")


if __name__ == '__main__':
    main()
