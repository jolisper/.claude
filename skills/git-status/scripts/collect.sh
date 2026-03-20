#!/usr/bin/env bash
set -euo pipefail

# Usage: bash ~/.claude/skills/git-status/scripts/collect.sh [--limit N] [--help]
#
# Collects all raw git status data in one pass.
# stdout format:
#   branch=<current-branch-or-HEAD>
#   status:
#   <git status --short lines>
#   log:
#   <git log --oneline -10 lines>
#   upstream=<branch-or-(no upstream)>
#   branches:
#   <branch> <upstream>   (one line per local branch, up to --limit)
#   (truncated at N)      (if limit was hit)
#   in-worktree=<true|false>
#   worktrees:            (only present when in-worktree=true)
#   <git worktree list --porcelain lines>

LIMIT=50

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --help)
      echo "Usage: bash ~/.claude/skills/git-status/scripts/collect.sh [--limit N]"
      echo "  --limit N   Max branches to list (default: 50). Prints truncation notice if hit."
      echo "  Outputs all git status data in structured sections."
      echo "  stdout sections: branch=, status:, log:, upstream=, branches:, in-worktree=, worktrees: (conditional)"
      exit 0 ;;
    *) echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

# Run all git commands in parallel
(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD") > "$tmpdir/branch" &
git status --short > "$tmpdir/status" 2>/dev/null &
(git log --oneline -10 2>/dev/null || true) > "$tmpdir/log" &
(git rev-parse --abbrev-ref @{upstream} 2>/dev/null || echo "(no upstream)") > "$tmpdir/upstream" &
git for-each-ref --format='%(refname:short) %(upstream:short)' refs/heads/ > "$tmpdir/refs" 2>/dev/null &
(git rev-parse --git-dir 2>/dev/null || echo ".git") > "$tmpdir/gitdir" &
git worktree list --porcelain > "$tmpdir/worktrees" 2>/dev/null &

wait

# Assemble output in section order
echo "branch=$(cat "$tmpdir/branch")"

echo "status:"
cat "$tmpdir/status"

echo "log:"
cat "$tmpdir/log"

echo "upstream=$(cat "$tmpdir/upstream")"

echo "branches:"
count=0
while IFS= read -r line; do
  if (( count >= LIMIT )); then
    echo "(truncated at $LIMIT)"
    break
  fi
  echo "$line"
  (( count++ )) || true
done < "$tmpdir/refs"

gitdir=$(cat "$tmpdir/gitdir")
if [[ "$gitdir" == *"/worktrees/"* ]]; then
  echo "in-worktree=true"
  echo "worktrees:"
  cat "$tmpdir/worktrees"
else
  echo "in-worktree=false"
fi
