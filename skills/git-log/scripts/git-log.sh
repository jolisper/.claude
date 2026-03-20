#!/usr/bin/env bash
# Usage:
#   scripts/git-log.sh                          — last 5 commits
#   scripts/git-log.sh --search TERM [--offset N] — search batch of 100

set -euo pipefail

SEARCH=""
OFFSET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --search) SEARCH="$2"; shift 2 ;;
    --offset) OFFSET="$2"; shift 2 ;;
    --help)
      echo "Usage: ~/.claude/skills/git-log/scripts/git-log.sh [--search TERM] [--offset N]"
      echo "  No args: show last 5 commits (git log --pretty=fuller --date=short)"
      echo "  --search TERM: scan 100 commits starting at --offset and print full"
      echo "                 details for each match"
      echo ""
      echo "Output (search mode):"
      echo "  Each matching commit is printed in full, preceded by a === MATCH === header."
      echo "  Final line: status=done match_count=N batch_count=M offset=O"
      echo "  If no more history: status=no_more_commits"
      exit 0 ;;
    *) echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── No-arg mode ────────────────────────────────────────────────────────────────
if [[ -z "$SEARCH" ]]; then
  git log -5 --pretty=fuller --date=short
  exit 0
fi

# ── Search mode ────────────────────────────────────────────────────────────────
BATCH=$(git log --oneline --skip="$OFFSET" -100 || true)

if [[ -z "$BATCH" ]]; then
  echo "status=no_more_commits"
  exit 0
fi

BATCH_COUNT=$(printf '%s\n' "$BATCH" | wc -l | tr -d ' ')

# grep exits 1 when no match — suppress that with || true
MATCH_HASHES=$(printf '%s\n' "$BATCH" | grep -i -- "$SEARCH" | awk '{print $1}' || true)

MATCH_COUNT=0
if [[ -n "$MATCH_HASHES" ]]; then
  MATCH_COUNT=$(printf '%s\n' "$MATCH_HASHES" | wc -l | tr -d ' ')
  while IFS= read -r hash; do
    printf '\n=== MATCH: %s ===\n' "$hash"
    git show --stat --pretty=fuller --date=short "$hash"
  done <<< "$MATCH_HASHES"
fi

printf '\nstatus=done match_count=%s batch_count=%s offset=%s\n' \
  "$MATCH_COUNT" "$BATCH_COUNT" "$OFFSET"
