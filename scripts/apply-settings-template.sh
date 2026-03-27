#!/usr/bin/env bash
set -e
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
  echo "Error: Python not found. Install Python 3 and try again." >&2
  exit 1
fi
"$PYTHON" "$(dirname "$0")/apply-settings-template.py" "$@"
