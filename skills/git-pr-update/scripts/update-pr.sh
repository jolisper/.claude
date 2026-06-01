#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: update-pr.sh --workspace <workspace> --repo <repo> --pr-id <id> --title <title> --description-file <file>
EOF
}

WORKSPACE=""
REPO=""
PR_ID=""
TITLE=""
DESC_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)        WORKSPACE="$2"; shift 2 ;;
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

require_arg "--workspace"        "$WORKSPACE"
require_arg "--repo"             "$REPO"
require_arg "--pr-id"            "$PR_ID"
require_arg "--title"            "$TITLE"
require_arg "--description-file" "$DESC_FILE"
require_arg "BITBUCKET_TOKEN"    "${BITBUCKET_TOKEN:-}"
require_arg "BITBUCKET_USERNAME" "${BITBUCKET_USERNAME:-}"

if [[ ! -f "$DESC_FILE" ]]; then
  echo "description file not found: $DESC_FILE" >&2
  exit 1
fi

PR_TITLE="$TITLE" PR_DESC="$(cat "$DESC_FILE")" \
python3 - <<'PYEOF' > /tmp/_pr_update_payload.json
import json, os
print(json.dumps({"title": os.environ["PR_TITLE"], "description": os.environ["PR_DESC"]}))
PYEOF

RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT -u "${BITBUCKET_USERNAME}:${BITBUCKET_TOKEN}" -H "Content-Type: application/json" "https://api.bitbucket.org/2.0/repositories/${WORKSPACE}/${REPO}/pullrequests/${PR_ID}" -d @/tmp/_pr_update_payload.json)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "$BODY"

case "$HTTP_CODE" in
  200) echo "status=updated" ;;
  401) echo "status=unauthorized" ;;
  403) echo "status=forbidden" ;;
  *) echo "status=error" ;;
esac
