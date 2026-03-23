---
name: git-commit-push
description: >
  Use this skill when the user wants to stage, commit, and push in one
  workflow. Invoke for requests like "commit and push", "push my changes",
  or "ship it". Runs the full commit protocol followed by the full push
  protocol.
disable-model-invocation: false
allowed-tools:
---

Stage changes, commit them with a Conventional Commits message, then push to the remote.

---

# Phase 1 — Commit

Invoke the `git-commit` skill to run the full commit protocol. Complete all commits before proceeding.

If the commit fails or the user aborts at any point, stop — do not proceed to Phase 2.

After all commits are done, ask the user:
"All commits done. Ready to push?" — wait for explicit confirmation. If the user says no or does not confirm, stop.

---

# Phase 2 — Push

Only proceed if Phase 1 completed successfully and the user confirmed.

Invoke the `git-push` skill to run the full push protocol.
