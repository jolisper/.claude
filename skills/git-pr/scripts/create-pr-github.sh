#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: create-pr-github.sh --repo OWNER/REPO --source S --destination D --title T --description-file F

Options:
  --repo              GitHub repository as OWNER/REPO
  --source            Source (head) branch name
  --destination       Destination (base) branch name
  --title             PR title
  --description-file  Path to a file containing the PR description (markdown)

Requires the GitHub CLI (gh) to be installed and authenticated (gh auth status).
Outputs the PR URL, then a line: status=created|unauthorized|error

Examples:
  create-pr-github.sh --repo myorg/my-repo --source feat/login --destination main \
    --title "feat(auth): add login page" --description-file /tmp/_pr_description.txt
EOF
}

REPO=""
SOURCE=""
DESTINATION=""
TITLE=""
DESC_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)              REPO="$2"; shift 2 ;;
    --source)            SOURCE="$2"; shift 2 ;;
    --destination)       DESTINATION="$2"; shift 2 ;;
    --title)             TITLE="$2"; shift 2 ;;
    --description-file)  DESC_FILE="$2"; shift 2 ;;
    --help|-h)           usage; exit 0 ;;
    *)                   echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$REPO" || -z "$SOURCE" || -z "$DESTINATION" || -z "$TITLE" || -z "$DESC_FILE" ]]; then
  echo "Error: all options are required." >&2
  usage
  exit 1
fi

if [[ ! -f "$DESC_FILE" ]]; then
  echo "Error: description file not found: $DESC_FILE" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh CLI is not installed." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "status=unauthorized"
  exit 0
fi

ERR_FILE=$(mktemp)
if URL=$(gh pr create \
  --repo "$REPO" \
  --head "$SOURCE" \
  --base "$DESTINATION" \
  --title "$TITLE" \
  --body-file "$DESC_FILE" 2>"$ERR_FILE"); then
  echo "$URL"
  echo "status=created"
else
  cat "$ERR_FILE" >&2
  echo "status=error"
fi
rm -f "$ERR_FILE"
