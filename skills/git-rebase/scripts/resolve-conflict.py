#!/usr/bin/env python3
"""Resolve git conflict markers in a file."""

import sys
import re
import os
import tempfile
import argparse


def strip_markers_keep_both(content):
    """Remove all conflict markers, keeping both sides verbatim."""
    content = re.sub(r'^<{7}[^\n]*\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^={7}\n', '', content, flags=re.MULTILINE)
    content = re.sub(r'^>{7}[^\n]*\n', '', content, flags=re.MULTILINE)
    return content


def replace_with_custom(content, resolution):
    """Replace the first conflict block with custom resolution text."""
    return re.sub(
        r'<{7}[^\n]*\n.*?>{7}[^\n]*\n',
        resolution,
        content,
        count=1,
        flags=re.DOTALL,
    )


def write_atomic(path, content):
    """Write content to path atomically via a sibling temp file."""
    dir_path = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=dir_path)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--file', metavar='PATH')
    parser.add_argument('--strategy', choices=['keep-both', 'custom'])
    parser.add_argument('--resolution-file', metavar='PATH')
    parser.add_argument('--help', action='store_true')
    args, unknown = parser.parse_known_args()

    if args.help:
        print('Usage: resolve-conflict.py --file PATH --strategy STRATEGY [--resolution-file PATH]')
        print('  Resolve git conflict markers in a file.')
        print('')
        print('  --file PATH              path to the conflicting file')
        print('  --strategy keep-both     strip markers, keep both sides verbatim')
        print('  --strategy custom        replace first conflict block with --resolution-file content')
        print('  --resolution-file PATH   path to file with resolved content (required for "custom")')
        print('')
        print('Examples:')
        print('  resolve-conflict.py --file src/foo.py --strategy keep-both')
        print('  resolve-conflict.py --file src/foo.py --strategy custom --resolution-file /tmp/res.txt')
        print('')
        print('Output: status=done file=<path> strategy=<strategy>')
        sys.exit(0)

    if unknown:
        print(f'Error: unknown argument: {unknown[0]}', file=sys.stderr)
        print('Try: resolve-conflict.py --help', file=sys.stderr)
        sys.exit(1)

    if not args.file:
        print('Error: --file is required.', file=sys.stderr)
        print('Try: resolve-conflict.py --help', file=sys.stderr)
        sys.exit(1)

    if not args.strategy:
        print('Error: --strategy is required (keep-both or custom).', file=sys.stderr)
        print('Try: resolve-conflict.py --help', file=sys.stderr)
        sys.exit(1)

    if args.strategy == 'custom' and not args.resolution_file:
        print('Error: --resolution-file is required when strategy is "custom".', file=sys.stderr)
        print('Try: resolve-conflict.py --help', file=sys.stderr)
        sys.exit(1)

    try:
        content = open(args.file).read()
    except OSError as e:
        print(f'Error: cannot read {args.file!r}: {e}', file=sys.stderr)
        print('Try: verify the file path is correct and the file is readable.', file=sys.stderr)
        sys.exit(1)

    if args.strategy == 'keep-both':
        resolved = strip_markers_keep_both(content)
    else:
        try:
            resolution = open(args.resolution_file).read()
        except OSError as e:
            print(f'Error: cannot read resolution file {args.resolution_file!r}: {e}', file=sys.stderr)
            print('Try: verify the resolution file exists and is readable.', file=sys.stderr)
            sys.exit(1)
        resolved = replace_with_custom(content, resolution)

    try:
        write_atomic(args.file, resolved)
    except Exception as e:
        print(f'Error: failed to write {args.file!r}: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'status=done file={args.file} strategy={args.strategy}')


if __name__ == '__main__':
    main()
