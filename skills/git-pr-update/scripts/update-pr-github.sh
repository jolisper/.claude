#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: update-pr-github.sh --repo <owner/repo> --pr-id <id> --title <title> --description-file <file>
EOF
}

REPO=""
PR_ID=""
TITLE=""
DESC_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)             REPO="$2"; shift 2 ;;
    --pr-id)            PR_ID="$2"; shift 2 ;;
    --title)            TITLE="$2"; shift 2 ;;
    --description-file) DESC_FILE="$2"; shift 2 ;;
    --help|-h)          usage; exit 0 ;;
    *)                  echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

require_arg() {
  local flag="$1" value="$2"
  if [[ -z "$value" ]]; then
    echo "$flag is required" >&2
    exit 1
  fi
}

require_arg "--repo"             "$REPO"
require_arg "--pr-id"            "$PR_ID"
require_arg "--title"            "$TITLE"
require_arg "--description-file" "$DESC_FILE"

if [[ ! -f "$DESC_FILE" ]]; then
  echo "description file not found: $DESC_FILE" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is not installed" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "status=unauthorized"
  exit 0
fi

ERR_FILE=$(mktemp)
if URL=$(gh pr edit "$PR_ID" \
  --repo "$REPO" \
  --title "$TITLE" \
  --body-file "$DESC_FILE" 2>"$ERR_FILE"); then
  echo "$URL"
  echo "status=updated"
else
  cat "$ERR_FILE" >&2
  echo "status=error"
fi
rm -f "$ERR_FILE"
