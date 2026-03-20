---
name: git-status
description: >
  Use this skill to get a concise overview of the current git working state.
  Invoke when the user asks "what changed", "git status", "show me changes",
  "what branch am I on", or wants a summary before committing or reviewing work.
  Shows: tracked/untracked changed files, a conceptual summary of the changes,
  and the branch hierarchy (parent branch upstream and child branches downstream).
disable-model-invocation: false
allowed-tools: Bash(bash:*)
---

## Step 1 — Gather raw data

Run this single command:

1. `bash ~/.claude/skills/git-status/scripts/collect.sh` — outputs all data in structured sections: `branch=<name>`, `status:` (git status --short lines), `log:` (recent commits), `upstream=<value>`, `branches:` (one `<branch> <upstream>` line per local branch, truncated at 50 with a notice), `in-worktree=<true|false>`, and — only when `in-worktree=true` — `worktrees:` (porcelain worktree list)

## Step 2 — Determine branch hierarchy

From the `branch=` line of the collect.sh output (command 1), you have the current branch name (call it `CURRENT`).

**Parent (upstream):** read the `upstream=` line from the collect.sh output (command 1). If its value is `(no upstream)`, note there is no configured upstream.

**Children (downstream):** scan the `branches:` lines from the collect.sh output (command 1) for any branch whose upstream column matches `CURRENT`. Those are branches that track the current branch.

## Step 3 — Determine other worktrees (conditional)

Check the `in-worktree=` line. If `false`, skip this step entirely.

If `true`, parse the `worktrees:` section. Each block contains `worktree <path>`, `HEAD <sha>`, and `branch <refname>` (or `detached`). List all entries whose `branch` does NOT match `refs/heads/<CURRENT>` — those are the other active checkouts in this repo.

## Step 4 — Synthesize a conceptual summary

Using the `status:` and `log:` sections from the collect.sh output (command 1), write 1–3 sentences describing *what* changed conceptually (not a list of files). Focus on intent: e.g. "Two files were modified to add authentication middleware; one new untracked test file is present." If there are no changes, say so clearly.

## Step 5 — Present the output

Use this format:

```
Branch: <current-branch>
  ↑ parent:   <upstream branch, or "none">
  ↓ children: <comma-separated child branches, or "none">

Other worktrees:      ← only include this block when in-worktree=true
  <branch> → <path>  (repeat per other active worktree)

Summary:
<1–3 sentence conceptual summary>

Changed files:
  Staged:    <list or "none">
  Modified:  <list or "none">
  Untracked: <list or "none">
```

Keep the output brief. Do not repeat raw git output verbatim.
