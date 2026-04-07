---
name: git-commit-push
description: >
  Use this skill when the user wants to stage, commit, and push in one
  workflow. Invoke for requests like "commit and push", "push my changes",
  or "ship it". Runs the full commit protocol followed by the full push
  protocol.
disable-model-invocation: true
allowed-tools: Read Bash(git status:*) Bash(git diff:*) Bash(git add:*) Bash(git commit:*) Bash(git log:*) Bash(python3:*) Bash(git rev-parse:*) Bash(git push:*) Bash(git fetch:*) Bash(bash ~/.claude/skills/git-push/scripts/:*)
---

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

Stage changes, commit them with a Conventional Commits message, then push to the remote.

This skill delegates to `git-commit` and `git-push` at runtime by reading their SKILL.md files.

## Pre-flight

Before starting, run `git rev-parse --abbrev-ref --symbolic-full-name @{u}`. If the command fails (no upstream set), warn the user and stop — do not begin committing work that cannot be pushed.

---

# Phase 1 — Commit

Read `~/.claude/skills/git-commit/SKILL.md` and follow its protocol in full. Complete all commits before proceeding.

If the commit fails or the user aborts at any point, stop — do not proceed to Phase 2.

After all commits are done, ask the user:
"All commits done. Ready to push?" — wait for explicit confirmation. If the user says no or does not confirm, stop.

---

# Phase 2 — Push

Only proceed if Phase 1 completed successfully and the user confirmed.

Read `~/.claude/skills/git-push/SKILL.md` and follow its protocol in full, with one override: **skip the pre-push confirmation prompt in Step 3** (the "Ready to push? (a) Push (b) Abort" menu) — the user already confirmed in Phase 1. Proceed directly to Step 4 (the push command).

If the push fails at any point: note to the user that their commits are already saved locally — no work is lost. Suggest running `/git-push` to retry the push separately when ready.
