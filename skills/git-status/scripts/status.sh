#!/usr/bin/env bash
set -euo pipefail

# Usage: bash ~/.claude/skills/git-status/scripts/status.sh [--help]
#
# Collects raw git status data in one pass.
# stdout format:
#   branch=<current-branch-or-HEAD>
#   status:
#   <git status --short lines>
#   log:
#   <git log --oneline -10 lines>
#   worktrees:
#   <git worktree list --porcelain lines>

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help)
      echo "Usage: bash ~/.claude/skills/git-status/scripts/status.sh"
      echo "  Outputs branch, status, log, and worktree data in structured sections."
      echo "  stdout sections: branch=, status:, log:, worktrees:"
      exit 0 ;;
    *) echo "Error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")
echo "branch=$branch"

echo "status:"
git status --short

echo "log:"
git log --oneline -10 2>/dev/null || true

echo "worktrees:"
git worktree list --porcelain
