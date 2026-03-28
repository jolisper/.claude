#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: create-pr.sh --workspace W --repo R --source S --destination D --title T --description-file F

Options:
  --workspace         Bitbucket workspace slug
  --repo              Bitbucket repository slug
  --source            Source branch name
  --destination       Destination (base) branch name
  --title             PR title
  --description-file  Path to a file containing the PR description (markdown)

Reads BITBUCKET_TOKEN from the environment.
Outputs the JSON response body, then a line: status=created|unauthorized|forbidden|error
EOF
}

WORKSPACE=""
REPO=""
SOURCE=""
DESTINATION=""
TITLE=""
DESC_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)         WORKSPACE="$2"; shift 2 ;;
    --repo)              REPO="$2"; shift 2 ;;
    --source)            SOURCE="$2"; shift 2 ;;
    --destination)       DESTINATION="$2"; shift 2 ;;
    --title)             TITLE="$2"; shift 2 ;;
    --description-file)  DESC_FILE="$2"; shift 2 ;;
    --help|-h)           usage; exit 0 ;;
    *)                   echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$WORKSPACE" || -z "$REPO" || -z "$SOURCE" || -z "$DESTINATION" || -z "$TITLE" || -z "$DESC_FILE" ]]; then
  echo "Error: all options are required." >&2
  usage
  exit 1
fi

if [[ ! -f "$DESC_FILE" ]]; then
  echo "Error: description file not found: $DESC_FILE" >&2
  exit 1
fi

if [[ -z "${BITBUCKET_TOKEN:-}" ]]; then
  echo "Error: BITBUCKET_TOKEN is not set." >&2
  exit 1
fi

if [[ -z "${BITBUCKET_USERNAME:-}" ]]; then
  echo "Error: BITBUCKET_USERNAME is not set." >&2
  exit 1
fi

DESCRIPTION=$(cat "$DESC_FILE")

PR_TITLE="$TITLE" PR_DESC="$DESCRIPTION" PR_SOURCE="$SOURCE" PR_DEST="$DESTINATION" \
python3 - <<'PYEOF' > /tmp/_pr_payload.json
import json, os
payload = {
    "title": os.environ["PR_TITLE"],
    "description": os.environ["PR_DESC"],
    "source": {"branch": {"name": os.environ["PR_SOURCE"]}},
    "destination": {"branch": {"name": os.environ["PR_DEST"]}}
}
print(json.dumps(payload))
PYEOF

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
  -u "${BITBUCKET_USERNAME}:${BITBUCKET_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.bitbucket.org/2.0/repositories/${WORKSPACE}/${REPO}/pullrequests" \
  -d @/tmp/_pr_payload.json)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "$BODY"

case "$HTTP_CODE" in
  201) echo "status=created" ;;
  401) echo "status=unauthorized" ;;
  403) echo "status=forbidden" ;;
  *)   echo "status=error" ;;
esac
