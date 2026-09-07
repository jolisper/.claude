#!/usr/bin/env bash
set -euo pipefail

# Usage: prepare-capture.sh --vault PATH --id ID [--tags tag1,tag2,...]
#   Ensures {vault}/notes and {vault}/@topics exist, creates any missing
#   tag stub files, and resolves an ID collision (appends a/b/c/... suffix
#   until {vault}/**/id: <id> is free).
#
# Output (stdout): status=done id=<final-id> tags_created=<n>
# Errors: printed to stderr, exit 1.

VAULT=""
ID=""
TAGS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vault) VAULT="$2"; shift 2 ;;
    --id) ID="$2"; shift 2 ;;
    --tags) TAGS="$2"; shift 2 ;;
    --help)
      echo "Usage: prepare-capture.sh --vault PATH --id ID [--tags tag1,tag2,...]"
      echo "  Ensures vault directories and tag stubs exist, resolves ID collisions."
      echo ""
      echo "Example:"
      echo "  prepare-capture.sh --vault /path/to/vault --id 202609071200 --tags obsidian-skill,rebase"
      exit 0 ;;
    *) echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$VAULT" ]]; then
  echo "Error: --vault is required." >&2
  exit 1
fi

if [[ -z "$ID" ]]; then
  echo "Error: --id is required." >&2
  exit 1
fi

mkdir -p "$VAULT/notes"
mkdir -p "$VAULT/@topics"

TAGS_CREATED=0
if [[ -n "$TAGS" ]]; then
  IFS=',' read -ra TAG_ARR <<< "$TAGS"
  for tag in "${TAG_ARR[@]}"; do
    stub="$VAULT/@topics/@${tag}.md"
    if [[ ! -f "$stub" ]]; then
      printf '# @%s\n' "$tag" > "$stub"
      TAGS_CREATED=$((TAGS_CREATED + 1))
    fi
  done
fi

FINAL_ID="$ID"
SUFFIXES=(a b c d e f g h i j k l m n o p q r s t u v w x y z)
idx=0
while grep -rq "^id: ${FINAL_ID}$" "$VAULT" 2>/dev/null; do
  if [[ $idx -ge ${#SUFFIXES[@]} ]]; then
    echo "Error: exhausted suffix range for id ${ID}." >&2
    exit 1
  fi
  FINAL_ID="${ID}${SUFFIXES[$idx]}"
  idx=$((idx + 1))
done

echo "status=done id=${FINAL_ID} tags_created=${TAGS_CREATED}"
