#!/usr/bin/env bash
set -euo pipefail

# Usage: bash ~/.claude/skills/git-status/scripts/gather.sh [--limit N] [--help]
#
# Outputs the upstream branch and full branch->upstream map.
# stdout format:
#   upstream=<branch-or-(no upstream)>
#   branches:
#   <branch> <upstream>   (one line per local branch, up to --limit)
#   (truncated at N)      (if limit was hit)

LIMIT=50

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --help)
      echo "Usage: bash ~/.claude/skills/git-status/scripts/gather.sh [--limit N]"
      echo "  --limit N   Max branches to list (default: 50). Prints truncation notice if hit."
      echo "  Outputs upstream branch and branch->upstream map."
      echo "  stdout:"
      echo "    upstream=<branch-or-(no upstream)>"
      echo "    branches:"
      echo "    <branch> <upstream>"
      echo "    (truncated at N)   -- if limit was reached"
      exit 0 ;;
    *) echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

upstream=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "(no upstream)")
echo "upstream=$upstream"

echo "branches:"
count=0
while IFS= read -r line; do
  if (( count >= LIMIT )); then
    echo "(truncated at $LIMIT)"
    break
  fi
  echo "$line"
  (( count++ )) || true
done < <(git for-each-ref --format='%(refname:short) %(upstream:short)' refs/heads/)
