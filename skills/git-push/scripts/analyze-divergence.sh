#!/usr/bin/env bash
set -euo pipefail

# Usage: analyze-divergence.sh [--help]
#
# Collects divergence data between the current branch and its upstream.
# Outputs structured sections the agent uses to classify the divergence.
#
# Output (stdout):
#   status=ok
#   ahead_count=N
#   behind_count=M
#   === AHEAD_SUBJECTS ===
#   <one commit subject per line>
#   === BEHIND_SUBJECTS ===
#   <one commit subject per line>
#   === REFLOG ===
#   <one reflog entry per line>
#
# Errors go to stderr with a non-zero exit code.

if [[ "${1:-}" == "--help" ]]; then
  echo "Usage: analyze-divergence.sh"
  echo "  Collects ahead/behind commit subjects and recent reflog for"
  echo "  divergence classification between HEAD and @{u}."
  echo ""
  echo "  No flags required. Upstream must already be set."
  echo ""
  echo "Example:"
  echo "  bash ~/.claude/skills/git-push/scripts/analyze-divergence.sh"
  echo ""
  echo "Output: structured sections on stdout; errors on stderr."
  exit 0
fi

# Verify upstream is set
if ! git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  echo "Error: no upstream configured for the current branch." >&2
  echo "Try: git push -u origin <branch> to set one." >&2
  exit 1
fi

# Collect commit subjects
ahead_subjects=$(git log @{u}..HEAD --format="%s" 2>&1) || {
  echo "Error: failed to read ahead commits: $ahead_subjects" >&2; exit 1
}
behind_subjects=$(git log HEAD..@{u} --format="%s" 2>&1) || {
  echo "Error: failed to read behind commits: $behind_subjects" >&2; exit 1
}
reflog=$(git reflog --format="%gd %gs" -30 2>&1) || {
  echo "Error: failed to read reflog: $reflog" >&2; exit 1
}

# Count
ahead_count=$(echo "$ahead_subjects" | grep -c . 2>/dev/null || echo 0)
behind_count=$(echo "$behind_subjects" | grep -c . 2>/dev/null || echo 0)

echo "status=ok"
echo "ahead_count=$ahead_count"
echo "behind_count=$behind_count"
echo "=== AHEAD_SUBJECTS ==="
echo "$ahead_subjects"
echo "=== BEHIND_SUBJECTS ==="
echo "$behind_subjects"
echo "=== REFLOG ==="
echo "$reflog"
