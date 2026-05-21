---
name: git-merge
description: >
  Use this skill when the user wants to merge a branch into the current branch.
  Invoke for requests like "merge X", "merge branch X", or "integrate branch X".
  Strictly fast-forward only — if histories have diverged, stops and directs the
  user to rebase first. Part of the git skill family.
disable-model-invocation: true
argument-hint: "[<branch>]"
allowed-tools: Bash(git rev-parse:*) Bash(git log:*) Bash(git merge:*) Bash(git status:*) Bash(git branch:*)
---

Merge a source branch into the current branch using fast-forward only. This skill
enforces a global linear-history policy: if the merge cannot fast-forward, the only
resolution is to rebase the source branch first — there is no merge-commit path.

**Rule**: Never use `cd`, `git -C`, `&&`, `||`, or pipes. One command per Bash call.
Rely on the shell's current working directory.

## Abort early if

- The repository has no other local branches to merge.
- A rebase or merge is already in progress (`git status` shows `MERGE_HEAD` or
  `REBASE_HEAD` exists).

## Step 1 — Resolve source branch

If `$ARGUMENTS` is non-empty, use it as the source branch name. Skip to Step 2.

Otherwise:
1. Run `git branch` to list local branches.
2. Exclude the current branch.
3. If exactly one other branch exists, propose it:
   ```
   Merge `<branch>` into current branch?
   (a) Yes
   (b) Cancel
   ```
4. If multiple branches exist, show a numbered list and ask:
   "Which branch do you want to merge in? Enter a number."

## Step 2 — Pre-flight

Run each command separately:

1. `git rev-parse --abbrev-ref HEAD` — note as `TARGET`.
2. `git status --short` — if non-empty:
   ```
   Your working tree has uncommitted changes.
   (a) Merge anyway
   (b) Cancel
   ```
   Stop on (b).
3. `git log <TARGET>..<source> --oneline` — if empty:
   "Branch `<source>` has no new commits to merge into `<TARGET>`." Stop.

## Step 3 — Fast-forward check

Run each command separately:

1. `git merge-base HEAD <source>`
2. `git rev-parse HEAD`
3. `git rev-parse <source>`

Evaluate:

- **`merge-base` == `<source>` tip** — `<TARGET>` already contains all commits
  from `<source>`. Say so and stop.
- **`merge-base` == HEAD** — fast-forward is possible. Proceed to Step 4.
- **Otherwise** — histories have diverged; fast-forward is not possible. Stop:
  ```
  ✗ Cannot fast-forward: <source> has diverged from <TARGET>.
    Rebase <source> onto <TARGET> first, then retry.
    Run: /git-rebase
  ```
  Even when the user insists, do not attempt a merge commit — this skill does
  not support that path. Direct them to /git-rebase.

## Step 4 — Confirm and merge

Show the commits about to land (`git log <TARGET>..<source> --oneline`) and ask:

```
Merge <source> → <TARGET>  [fast-forward]
  <hash>  <subject>
  <hash>  <subject>

(a) Merge
(b) Cancel
```

Stop on (b).

On (a): run `git merge --ff-only <source>`.

## Step 5 — Interpret the result

- **Exit 0** — show: `Merged <source> into <TARGET> (fast-forward).`
  Then show `git log ORIG_HEAD..HEAD --oneline` to confirm what landed.
- **Non-zero exit** — show the full stderr output. If it contains
  "Not possible to fast-forward": the branches diverged between the pre-flight
  check and the merge (e.g. another process pushed). Suggest running
  `/git-rebase` then retrying. For any other error: explain the likely cause.
