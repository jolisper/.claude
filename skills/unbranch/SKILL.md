---
name: unbranch
description: >
  Use this skill when the user wants to return to the conversation they
  branched from — e.g. "go back to the previous conversation", "un-branch",
  "return to the original session". Checks whether the current session was
  created via /branch, and if so surfaces the /resume command to switch back
  to the parent conversation.
disable-model-invocation: true
when_to_use: >
  User wants to return to the conversation they branched from — after
  finishing exploratory work in a session created via /branch.
allowed-tools: Bash(bash ~/.claude/skills/unbranch/scripts/find-parent.sh:*)
---

## Step 1 — Look up the parent session

Run this single command:

1. `bash ~/.claude/skills/unbranch/scripts/find-parent.sh` — scans this session's own transcript for the `Use /resume <id> to return to the original` line that `/branch` prints when a branch is created, and either:
   - exits non-zero with `error: ...` on stderr — could not locate this session's transcript
   - or prints to stdout one of:
     - `not-a-branch=true` — this session was not created via `/branch`
     - `parent_session_id=<uuid>`, `branch_name=<name>`, and `copied=true|false` — this session is a branch; `<uuid>` is the original session to return to; `copied=true` means `/resume <uuid>` was already placed on the clipboard via `pbcopy`

## Step 2 — Report

- **Non-zero exit / `error: ...` on stderr**: Tell the user the parent session couldn't be determined (relay the stderr message), and stop.
- **`not-a-branch=true`**: Tell the user this conversation wasn't created with `/branch`, so there's no parent to return to.
- **`parent_session_id=<uuid>` with `copied=true`**: Respond with **only** this literal text and nothing else — no other prose, no explanation, no code fence, no `branch_name`:

  `Copied to clipboard: /resume <uuid>`

- **`parent_session_id=<uuid>` with `copied=false`** (no `pbcopy` available): Respond with **only** this literal text and nothing else — no prose, no explanation, no code fence, no `branch_name`, just the command on its own line so the user can copy-paste it directly:

  `/resume <uuid>`

  Do not attempt to run `/resume` yourself — it's a REPL command the user runs, not a tool call.
