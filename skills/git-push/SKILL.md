---
name: git-push
description: >
  Use this skill when the user wants to push the current branch to its remote.
  Invoke for requests like "push", "push my changes", or "push to origin".
  Detects divergence and handles rebased, amended, and genuinely diverged branches.
disable-model-invocation: true
allowed-tools: Bash(git:*) Bash(bash:*)
---

Push the current branch to its remote. Follow this protocol:

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

## Step 1 — Pre-flight check

Run each of these commands separately:

1. `git rev-parse --abbrev-ref HEAD` — note the current branch name.
2. `git rev-parse --abbrev-ref --symbolic-full-name @{u}` — if this command fails (non-zero exit or error output), treat upstream as not set.

## Step 2 — Handle missing upstream

If the upstream is not set:
- Suggest: `git push -u origin <branch>` (using the current branch name).
- Ask the user to confirm before proceeding.
- After confirmation, proceed to Step 4.

## Step 3 — Detect divergence

If the upstream is set, run both of these commands separately:

1. `git log @{u}..HEAD --oneline` — commits ahead (local has, remote doesn't).
2. `git log HEAD..@{u} --oneline` — commits behind (remote has, local doesn't).

Interpret:
- **Ahead only** (ahead > 0, behind = 0) — normal push. Show the pending commits, then ask:
  ```
  Ready to push? (a) Push  (b) Abort
  ```
  If (a): proceed to Step 4. If (b): stop.
- **Nothing to push** (ahead = 0, behind = 0) — say "Nothing to push" and stop.
- **Behind only** (ahead = 0, behind > 0) — say "Your branch is behind the remote. Run `/git-pull` first." and stop.
- **Diverged** (ahead > 0, behind > 0) — the histories have diverged. Perform a **rebase analysis** to determine the cause:

  1. Run `bash ~/.claude/skills/git-push/scripts/analyze-divergence.sh` (run `--help` first to confirm the interface). Read `ahead_count`, `behind_count`, the `AHEAD_SUBJECTS` section (local-only commit subjects), the `BEHIND_SUBJECTS` section (remote-only commit subjects), and the `REFLOG` section (recent reflog entries — look for `rebase (start): checkout <branch>` entries identifying the rebase target).
  2. Identify the rebase base branch from the `REFLOG` section: look for the most recent `rebase (start): checkout <branch>` entry and extract `<branch>`. If not found, try the local-only subjects for merge commit messages (e.g. `Merge branch 'main' into ...`). If still not found, run `git merge-base HEAD @{u}` then `git branch -a --contains <hash> --no-contains HEAD` to find candidate branches. If none succeed, the base branch is unknown.
  3. Compare the two lists of subjects. Classify the divergence:
     - **Rebase detected** — most subjects appear in both lists (same messages, different hashes). Always include the base branch if identified (from step 2): "This looks like a rebase onto `<base>` — the remote has N commit(s) that were rewritten locally (same messages, different hashes). Force push with lease is the standard resolution." If the base branch is unknown, say "onto an unknown base" instead.
     - **Amend detected** — the local side has fewer commits and the top commit subject matches a remote subject. Report: "This looks like an amended commit — the remote has the original version. Force push with lease is the standard resolution."
     - **Genuine divergence** — the subjects are mostly different, meaning someone else pushed new work or the local branch has truly new commits alongside remote-only commits. Report: "The local and remote branches have genuinely different commits. Pulling (merge or rebase) is likely the right approach."
  4. Present the analysis and ask the user. The header line **must** name the exact local branch and the remote branch that will be overwritten (use the values from Step 1):
     ```
     Your branch and the remote have diverged (<N> ahead, <M> behind).
     <analysis result from above>
     ⚠️  Force push will overwrite: <remote>/<branch>  (local: <branch>)
     (a) Force push with lease (safe — aborts if someone else pushed in the meantime)
     (b) Pull first (creates a merge — use this if you did NOT rebase)
     (c) Abort
     ```
  - If (a): proceed to Step 4 with force-with-lease.
  - If (b): tell the user to run `/git-pull` first, then push again. Stop.
  - If (c): stop.

## Step 4 — Push

Choose the push command based on prior steps:
- No upstream set → `git push -u origin <branch>`
- Normal push → `git push`
- Force-with-lease (user chose option (a) in Step 3) → `git push --force-with-lease`

## Step 5 — Interpret the result

Report exactly one of these outcomes:

- **Success** — show the branch name and remote confirmation from the command output.
- **Rejected (non-fast-forward)** — explain that the remote has commits the local branch does not. Run Step 3's divergence detection (if not already done) to determine if this is a rebase scenario, and present the appropriate options.
- **Rejected (force-with-lease)** — someone else pushed to the remote since your last fetch. Suggest running `git fetch` to update, reviewing the new remote commits, then retrying.
- **Auth / network error** — show the error message and suggest checking SSH keys or credentials.
- **Other error** — show stderr and explain the likely cause.
