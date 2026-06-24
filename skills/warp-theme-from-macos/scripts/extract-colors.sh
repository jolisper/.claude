#!/usr/bin/env bash
set -euo pipefail

# extract-colors.sh — Wrapper that invokes extract-colors.py.
# Usage: extract-colors.sh --thumbnail <path> [--alt]

SCRIPT_DIR="$(dirname "$0")"
exec python3 "$SCRIPT_DIR/extract-colors.py" "$@"
