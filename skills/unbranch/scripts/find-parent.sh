#!/bin/bash
set -euo pipefail

# Usage: find-parent.sh
#
# Checks whether the current Claude Code session (from $CLAUDE_CODE_SESSION_ID)
# was created via /branch, by scanning its own transcript for the
# "Use /resume <id> to return to the original" line that /branch prints.
#
# Output (stdout, key=value):
#   not-a-branch=true                          — this session was not created via /branch
#   parent_session_id=<uuid>                   — the session this one was branched from
#   branch_name=<name>                         — the name /branch gave this session
#
# On failure, writes "error: <what was expected> — <what to try>" to stderr and exits 1.
if [ "${1:-}" = "--help" ]; then
  echo "Usage: find-parent.sh"
  echo "  No flags. Reads \$CLAUDE_CODE_SESSION_ID and the current session's own"
  echo "  transcript under ~/.claude/projects/ to find the session it was /branch'd from."
  exit 0
fi

if [ -z "${CLAUDE_CODE_SESSION_ID:-}" ]; then
  echo "error: expected \$CLAUDE_CODE_SESSION_ID to be set by Claude Code — check this is running inside a Claude Code session" >&2
  exit 1
fi

FILE=$(find ~/.claude/projects -name "${CLAUDE_CODE_SESSION_ID}.jsonl" 2>/dev/null | head -1)

if [ -z "$FILE" ]; then
  echo "error: expected a transcript at ~/.claude/projects/*/${CLAUDE_CODE_SESSION_ID}.jsonl — check the session has written at least one message" >&2
  exit 1
fi

# NOTE: this depends on the exact, undocumented wording /branch prints on branch
# creation. If /unbranch starts wrongly reporting not-a-branch=true for sessions
# you know were branched, check whether Claude Code changed this message text.
MATCH=$(grep -o 'Use /resume [0-9a-f-]\{36\} to return to the original' "$FILE" | tail -1 || true)

if [ -z "$MATCH" ]; then
  echo "not-a-branch=true"
  exit 0
fi

PARENT_ID=$(echo "$MATCH" | grep -o '[0-9a-f-]\{36\}')
NAME=$( (grep -o 'Branched conversation \\"[^"]*\\"' "$FILE" || true) | tail -1 | sed -e 's/^Branched conversation \\"//' -e 's/\\"$//')
NAME="${NAME:-unnamed}"

echo "parent_session_id=$PARENT_ID"
echo "branch_name=$NAME"
