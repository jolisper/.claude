#!/usr/bin/env bash
# python-clean.sh — Remove Python build artifacts (__pycache__ dirs and .pytest_cache)
#
# Usage:
#   bash python-clean.sh [--help]
#
# Flags:
#   --help    Print this help message and exit
#
# Examples:
#   bash ~/.claude/skills/run-tests/scripts/python-clean.sh
#
# Output (stdout):
#   status=done
#
# Errors go to stderr with a non-zero exit code.

set -euo pipefail

if [[ "${1:-}" == "--help" ]]; then
  grep '^#' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi

find . -type d -name __pycache__ -not -path './.git/*' -prune -exec rm -rf {} +
rm -rf .pytest_cache

echo "status=done"
