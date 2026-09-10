---
name: git-reshape
description: >
  Use this skill when the user explicitly asks to reshape, reorganize, or
  reorder the commits on the current branch into a coherent functional
  history — grouping, splitting, squashing, and rewording commits so related
  work reads together instead of in incidental development order. Invoke for
  requests like "reshape my commits", "reorganize this branch's history into
  logical order", "give these commits functional semantic", or "/git-reshape".
  Never invoke proactively — this rewrites history and always requires
  explicit user confirmation before touching anything.
disable-model-invocation: true
when_to_use: >
  Trigger when the current branch's commits are in incidental development
  order (typos, wip, fixups, out-of-order work) and need regrouping into a
  functional, logically-ordered history before review or merge.
argument-hint: "target branch (optional)"
allowed-tools: Bash(git status:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git branch:*) Bash(git fetch:*) Bash(git merge-base:*) Bash(git reset:*) Bash(git add:*) Bash(git diff:*) Bash(git stash:*) Bash(git show:*) Bash(git checkout:*) Bash(python3:*) Read Write Edit
effort: high
---

Reshape the commits on the current branch (since it diverged from its base) into new commits grouped by functional purpose, in an order that tells a coherent build-up story — instead of the incidental order they were developed in.

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

## Dependencies

This skill reuses two scripts owned by sibling skills rather than re-implementing their logic (cluster consistency):
- `~/.claude/skills/git-commit/scripts/stage-hunks.py` — for intra-file hunk-level staging, called internally by `apply-plan.py` in Step 4.
- `~/.claude/skills/git-rebase/scripts/resolve-conflict.py` — for "keep both" resolution during stash-pop conflicts in Step 6.

It also owns three scripts of its own:
- `~/.claude/skills/git-reshape/scripts/detect-base.py` — base-branch detection in Step 1.
- `~/.claude/skills/git-reshape/scripts/apply-plan.py` — executes the confirmed reshape plan in Step 4.
- `~/.claude/skills/git-reshape/scripts/run-checks.py` — optional build/test check in Step 6.

If any of these scripts is missing, tell the user which one and stop before that step — do not attempt to hand-roll the equivalent logic inline.

## When NOT to use this skill / when to abort

- The commit range ahead of base contains merge commits — reshape only supports a linear range. Stop and ask the user to resolve/flatten separately first.
- There are zero commits ahead of the detected base — report "No commits to reshape" and stop. A range of exactly **one** commit is not grounds to stop: that commit may still bundle unrelated concerns worth splitting into several. Don't assume "only 1 commit ahead" means there's nothing to reshape — proceed to Step 3 and cluster it like any other range.
- The user has not explicitly confirmed the proposed plan (Step 3) — never proceed to Step 4 without an explicit "(a) Apply this plan".

## Step 1 — Pre-flight check

**Target branch override**: If `$ARGUMENTS` is set and non-empty, use it as the base branch and skip auto-detection below.

Run each of these commands separately:

1. `git status`
2. `git rev-parse --abbrev-ref HEAD` — note the current branch name.
3. **Detect the base branch** (skip if `$ARGUMENTS` provided): run `python3 ~/.claude/skills/git-reshape/scripts/detect-base.py --branch <current-branch>`. On `status=found`, use the reported `base`. On `status=ambiguous`, ask the user which branch is the base.
4. **Shared-branch guard**: `git branch -r --list origin/<current-branch>`. If the remote branch exists, warn:
   ```
   ⚠ Warning: `<current-branch>` exists on the remote. Reshaping rewrites history,
   causing divergence for anyone else tracking this branch.

   How do you want to proceed?
   (a) Proceed — I understand this branch is shared and intend to rewrite its history
   (b) Abort
   ```
   Show this warning even if the user already explicitly asked for a reshape — they may not have considered that others track this branch. On (b): stop.
5. `git fetch origin`, then `git merge-base HEAD origin/<base>` — note the result as `<merge-base>`.
6. `git log <merge-base>..HEAD --oneline` — if empty, report "No commits to reshape" and stop. If it shows exactly one commit, do **not** stop — a single commit can still bundle unrelated concerns; proceed to Step 3 and let clustering decide whether it splits into multiple commits.
7. `git log <merge-base>..HEAD --merges --oneline` — if this returns any commits, stop and tell the user reshape only supports a linear commit range; ask them to resolve/flatten merges first.

## Step 2 — Handle dirty working tree

If `git status` (from Step 1) shows uncommitted changes:
- Tell the user what changed and ask whether to (a) stash changes, reshape, then restore, or (b) abort.
- If stash: run `git stash -u`, continue, then `git stash pop` in Step 6.
- Do not reshape over a dirty tree.

## Step 3 — Backup, analyze, and propose

1. **Create a backup ref** before anything destructive happens: `git branch reshape-backup-<current-branch>-<short-sha-of-HEAD>` (use `git rev-parse --short HEAD` for the sha). This is silent — don't ask permission, just do it, then mention it in the final summary.
2. **Read every commit in range**: `git log <merge-base>..HEAD -p` (or iterate `git show` per commit) to understand what each commit's diff actually does.
3. **Cluster into semantic groups**, tracking at the hunk level (not the file level) so hunks from different original commits can merge into one output group, and a single file's hunks can split across multiple output groups:
   - Group by shared feature/fix/refactor purpose, regardless of which original commit a hunk came from.
   - Test files group with the production code they test.
   - Config/build changes stay separate unless directly required by a feature group.
   - Order groups so the result reads as a logical build-up: foundational/refactor changes before the feature that depends on them, feature before its tests, docs last. This ordering is the primary value of the skill — don't just preserve original commit order for convenience.
4. **Present the plan and wait — do not proceed without an explicit choice, even if the reshape looks obvious or the user seems in a hurry:**
   ```
   Proposed reshape (N original commits → M new commits):

   ── Commit 1: <type>(scope): <description> ──
      • <file1> — <what/why>
      • <file2> (from original commits <sha>, <sha>) — <what/why>

      Reason: <why these changes belong together and go first>

   ── Commit 2: <type>(scope): <description> ──
      ...

   (a) Apply this plan
   (b) Edit grouping — tell me what to change
   (c) Abort — leave history untouched
   ```
   On (b): revise the plan per the user's feedback and show it again before proceeding. On (c): stop; the backup branch from step 1 can be deleted (`git branch -D reshape-backup-...`) since nothing was touched. There is no auto-mode for this skill — always show this menu and wait, unlike `git-commit`'s `--auto` flag.

## Step 4 — Execute the rewrite

Only after the user picks "(a) Apply this plan" (or an edited version of it):

1. `git reset --soft <merge-base>` — collapses the whole range into staged changes. This is deliberately not an interactive rebase: because commits are not being replayed, there are no rebase conflicts to resolve here, no matter how much reordering or splitting the plan calls for.
2. Write the confirmed plan to a JSON file: a list of groups, each with `message` (the Conventional Commits message) and either `files` (whole-file groups) or `hunks` (a list of `{"file": <path>, "hunks": [N,...]}` for intra-file splits, 1-based hunk numbers matching the order they appear in `git diff <file>`), in the planned order.
3. Run `python3 ~/.claude/skills/git-reshape/scripts/apply-plan.py --plan <path-to-json>`. This loops reset/add-or-stage-hunks/commit per group internally, so the working tree ends up clean with every planned group committed in order.

If the script exits non-zero, stop immediately, report its stderr error and which group failed (it prints `status=done group=N` for each committed group, so N+1 is where it stopped), and tell the user the backup branch is intact — do not attempt to auto-recover mid-loop.

## Step 5 — Verification

`git diff reshape-backup-<current-branch>-<sha> HEAD` — this must produce **no output**. It proves the rewrite changed only history shape (grouping, order, messages), not the net content of the branch.

- If it is empty: proceed to Step 6.
- If it is **not** empty: stop immediately. Report the exact diff to the user, state that the backup branch `reshape-backup-<current-branch>-<sha>` is untouched and safe, and do not attempt to auto-fix. Even if the discrepancy looks trivial (e.g. whitespace), still stop and report it — a silent content change defeats the entire point of this verification step.

## Step 6 — Summary

1. Show the new commit sequence: `git log <merge-base>..HEAD --oneline`.
2. State the backup branch name and how to revert if needed: `git reset --hard reshape-backup-<current-branch>-<sha>`, then delete the backup once confident with `git branch -D reshape-backup-<current-branch>-<sha>`.
3. If a stash was used in Step 2, run `git stash pop`:
   - If it conflicts, resolve one file at a time: classify each via `git status --short` (`UU` content conflict, `DU`/`UD` structural, `AA` add/add), show the conflicting section and a recommended resolution, then offer:
     ```
     How do you want to resolve <file>?
     (a) Keep ours
     (b) Keep theirs
     (c) Keep both
     (d) Edit manually
     (e) Abort
     ```
     For (a)/(b): `git checkout --ours|--theirs <file>` then `git add <file>`. For (c): use `python3 ~/.claude/skills/git-rebase/scripts/resolve-conflict.py --file <file> --strategy keep-both`, then `git add <file>`. For (d): apply the fix with the Edit tool (or ask the user to edit and confirm), then `git add <file>`. For (e): stop — the reshape itself already succeeded; only the stash restore is abandoned, so tell the user their stashed changes remain safe in the stash list.
     After each resolution, run `git diff --check <file>` to confirm no markers remain before moving to the next file.
   - Once resolved (or if it applied cleanly), confirm the stash pop succeeded.
4. Ask:
   ```
   Reshape complete. Want me to run a quick build/test check to catch semantic issues?
   (a) Yes — run build/tests
   (b) No — skip
   ```
   On (a): run `python3 ~/.claude/skills/git-reshape/scripts/run-checks.py` and report `status=pass`/`status=fail`/`status=none` along with the command's output. On (b): note that a clean reshape only guarantees the net diff is unchanged, not that the new commit boundaries build/test cleanly in isolation.
