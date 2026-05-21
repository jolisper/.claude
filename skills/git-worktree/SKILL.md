---
name: git-worktree
description: >
  Use this skill to manage git worktrees — add, list, remove, prune, and close
  out a worktree branch. Invoke for requests like "new worktree for <branch>",
  "list my worktrees", "close this worktree", "remove worktree X", or "prune
  stale worktrees". Context-aware: adapts behavior when invoked from inside a
  worktree.
disable-model-invocation: true
argument-hint: "[add <branch> [path] | list | remove <branch> | prune | close [<branch>] [--force]]"
allowed-tools: Bash(git worktree:*) Bash(git rev-parse:*) Bash(git branch:*) Bash(git log:*) Bash(git status:*) Bash(git merge:*) Bash(git -C:*) Read
skills: git-merge
when_to_use: >
  Invoke when the user wants to add, list, remove, prune, or close out a git
  worktree, or asks about managing multiple checkouts of a repository.
effort: high
---

Full worktree lifecycle management. Enforces a linear-history policy: `close`
merges via fast-forward only and rejects unpushed branches (unless `--force`).

**Rule**: Never use `&&`, `||`, or pipes. One command per Bash call.
`git -C <path>` is explicitly permitted for targeting specific worktrees.

## Context detection (runs before every subcommand)

1. `git rev-parse --git-dir` — if the output path contains `/worktrees/`,
   set `IN_WORKTREE=true`; otherwise `IN_WORKTREE=false`.
2. `git rev-parse --git-common-dir` — strip the trailing `/.git` segment to get
   `MAIN_REPO` (e.g. `/path/to/repo/.git` → `/path/to/repo`).

Both values are available to all subcommand steps.

## Subcommand dispatch

Parse the first word of `$ARGUMENTS`:

| First word | Subcommand |
|---|---|
| `add` | **add** |
| `remove` | **remove** |
| `prune` | **prune** |
| `close` | **close** |
| `list` or empty | **list** |

---

## add

**Step 1 — Resolve branch**

Run `git branch --list <branch>`. Non-empty output → branch exists, use as-is.
Empty output → new branch; create from current HEAD.

For new branches only: validate the name against the Conventional Branch spec.
Read `~/.claude/skills/git-new-branch/references/conventional-branch-spec.md`.
List each rule violated and ask for a corrected name. Repeat until all rules pass.

**Step 2 — Resolve path**

If `$ARGUMENTS` contains a path after the branch name, use it directly.

Otherwise derive the default:
1. `git rev-parse --show-toplevel` → `<repo-root>`
2. Last path component of `<repo-root>` → `<repo-name>`
3. Slugify `<branch>`: replace `/` with `-`, lowercase → `<slug>`
4. Path = `<repo-root>/../<repo-name>-<slug>`

Show the resolved path and confirm:
```
Create worktree at <path>?
(a) Yes
(b) Cancel
```
Stop on (b).

**Step 3 — Create**

- Existing branch: `git worktree add <path> <branch>`
- New branch: `git worktree add -b <branch> <path>`

On non-zero exit: show the git error and stop.

**Step 4 — Confirm**
```
Worktree created:
  Branch: <branch>
  Path:   <path>
```

---

## list

1. `git rev-parse --show-toplevel` → current worktree path (to mark with `*`).
2. `git branch --list main` → non-empty: `MAIN_BRANCH=main`, else `MAIN_BRANCH=master`.
3. `git worktree list --porcelain` — parse each blank-line-separated block:
   extract `worktree <path>`, `HEAD <sha>`, and `branch <refname>` or `detached`.
4. For each worktree: `git -C <path> status --short` — non-empty: dirty; empty: clean.
5. For each non-main worktree (skip detached HEAD): `git log <MAIN_BRANCH>..<branch> --oneline`
   — non-empty: ahead; empty: synced.

Display with aligned columns. Compute column widths from the actual data:
- **W1** = longest branch name across all worktrees
- **W2** = longest path across all worktrees (after replacing `$HOME` with `~`)

```
Worktrees:

  * main           ~/.claude                          4b7fd0a  (dirty)
    bolson-ravine  ~/.warp/worktrees/.claude/branch   bc2501b  (dirty, synced)
    feat/auth      ~/projects/myapp-feat-auth         a3f91d2  (clean, ahead)
```

Format each row as: `  <marker> <branch padded to W1>  <path padded to W2>  <sha>  <status>`
where `<marker>` is `*` for the current worktree and ` ` otherwise.

Replace `$HOME` with `~`. Show first 7 sha chars.
- Main worktree: show `(dirty)` or `(clean)` only — divergence against itself is meaningless.
- Non-main worktrees: show `(dirty, ahead)`, `(clean, ahead)`, `(dirty, synced)`, or `(clean, synced)`.
- Detached HEAD: show `(detached HEAD)` — skip divergence check.

---

## remove

1. Parse `<branch>` from `$ARGUMENTS` after `remove`.
2. `git worktree list --porcelain` — find the block where `branch` matches
   `refs/heads/<branch>`. Extract its `worktree <path>`.
   If not found: "No worktree found for branch `<branch>`." Stop.
3. If `IN_WORKTREE=true` and `<branch>` matches the current branch:
   "You are inside this worktree. Use `close` to merge and remove it, or switch
   to another worktree first." Stop.
4. `git -C <path> status --short` — if non-empty:
   ```
   The worktree at <path> has uncommitted changes:
   <status lines>

   (a) Remove anyway
   (b) Cancel
   ```
   Stop on (b).
5. `git worktree remove <path>`. On non-zero exit: show the error and stop.
6. "Worktree removed: `<path>`"

---

## prune

**Step 1 — Remove stale records**

1. `git worktree prune --verbose`.
2. Empty output: "Nothing to prune — all worktree records are valid."
   Non-empty: show the full output.

**Step 2 — Detect prunable worktrees**

1. `git branch --list main` → non-empty: `MAIN_BRANCH=main`, else `MAIN_BRANCH=master`.
2. `git worktree list --porcelain` — collect all non-main worktrees.
3. For each: `git log <MAIN_BRANCH>..<branch> --oneline`. Empty → synced.
4. If no synced worktrees: stop.
5. For each synced worktree: `git -C <path> status --short`.
   - Empty → **clean + synced** (prunable)
   - Non-empty → **dirty + synced** (warn before removing)
6. If `IN_WORKTREE=true` and the current branch is synced, mark it "(current — skipping)"
   and exclude it. If all candidates were skipped: stop.
7. Show candidates grouped:
   ```
   Prunable worktrees:

     <branch>  <path>  (clean, synced)

   Prunable with uncommitted changes:

     <branch>  <path>  (dirty, synced)
   ```
   Omit a group header if that group is empty.
8. Ask based on which groups are present:

   *Only clean+synced:*
   ```
   Remove them?
   (a) Remove all
   (b) Cancel
   ```

   *Only dirty+synced:*
   ```
   These worktrees have uncommitted changes that will be lost. Remove them?
   (a) Remove anyway
   (b) Cancel
   ```

   *Both groups:*
   ```
   (a) Remove clean only
   (b) Remove all (including dirty)
   (c) Cancel
   ```

   Stop on Cancel.

9. For each approved worktree: `git worktree remove <path>`.
   On non-zero exit: show the error and continue to the next — do not abort the batch.
10. `git worktree prune`.
11. "Removed N worktree(s)."

---

## close

Full close-out: merge → branch delete → worktree remove. Stops on any failure.
No step auto-rolls back a previous one.

**Step 1 — Pre-flight**

1. `git rev-parse --abbrev-ref HEAD` → `CURRENT`.
2. Resolve `TARGET`:
   - Branch name after `close` in `$ARGUMENTS` → use it.
   - No branch name and `CURRENT` is not `main`/`master` → use `CURRENT`.
     Tell the user: "Closing current branch: `<CURRENT>`."
   - No branch name and `CURRENT` is `main`/`master` → ask:
     "Which branch do you want to close out?"
3. `git branch --list <TARGET>` — empty: "Branch `<TARGET>` not found." Stop.
4. `git branch --list main` — non-empty: `MAIN_BRANCH=main`, else `MAIN_BRANCH=master`.
5. Set `CLOSING_FROM_INSIDE = (IN_WORKTREE=true AND TARGET == CURRENT)`.
6. Unpushed commits check — skip if `--force` is in `$ARGUMENTS`:
   `git log origin/<TARGET>..<TARGET> --oneline`
   If non-empty:
   ```
   ✗ Branch <TARGET> has N unpushed commit(s). Push before closing out.
     Run /git-push, then retry. Use --force to override.
   ```
   Stop.

**Step 2 — Merge**

*Normal mode* (`CLOSING_FROM_INSIDE=false`):

Run `git rev-parse --abbrev-ref HEAD`. If not `MAIN_BRANCH`:
"Switch to `<MAIN_BRANCH>` before closing out." Stop.

Read `~/.claude/skills/git-merge/SKILL.md` and follow its full protocol with
`<TARGET>` as the source branch. (git-merge uses only git Bash commands and Read;
all required tools are covered by this skill's allowed-tools.) If the merge fails
or the user cancels: stop. Do not proceed to Step 3.

*Closing-from-inside mode* (`CLOSING_FROM_INSIDE=true`):

1. `git -C <MAIN_REPO> rev-parse --abbrev-ref HEAD` — must equal `MAIN_BRANCH`.
   If not: "The main repo is on `<other>`, not `<MAIN_BRANCH>`. Switch it first." Stop.
2. `git -C <MAIN_REPO> log <MAIN_BRANCH>..<TARGET> --oneline` — show commits.
3. Confirm:
   ```
   Merge <TARGET> → <MAIN_BRANCH>  [fast-forward]
   (a) Merge
   (b) Cancel
   ```
   Stop on (b).
4. `git -C <MAIN_REPO> merge --ff-only <TARGET>`.
   On non-zero exit: show the error and stop.

**Step 3 — Delete branch**

```
Delete branch <TARGET>?
(a) Delete
(b) Cancel
```
Stop on (b).

*Normal mode:* `git branch -d <TARGET>`
*Closing-from-inside mode:* `git -C <MAIN_REPO> branch -d <TARGET>`

On failure: show the error and stop — do not force-delete.

**Step 4 — Remove worktree**

*Normal mode:* `git worktree list --porcelain`
*Closing-from-inside mode:* `git -C <MAIN_REPO> worktree list --porcelain`

Find the block for `refs/heads/<TARGET>`. If not found:
"No worktree found for `<TARGET>` — skipping removal." Skip to Step 5.

*Normal mode confirmation:*
```
Remove worktree at <path>?
(a) Remove
(b) Cancel
```

*Closing-from-inside mode confirmation:*
```
⚠ Removing this worktree will delete your current working directory (<path>).
(a) Remove
(b) Cancel
```

Stop on (b).

*Normal mode:*
Run `git worktree remove <path>`.
Run `git worktree prune`.

*Closing-from-inside mode:*
Run `git -C <MAIN_REPO> worktree remove <path>`.
Run `git -C <MAIN_REPO> worktree prune`.

On non-zero exit at any point: show the error and stop.

**Step 5 — Summary**

```
Close-out complete:
  ✓ Merged <TARGET> into <MAIN_BRANCH> (fast-forward)
  ✓ Deleted branch <TARGET>
  ✓ Removed worktree <path>
```

Omit the worktree line if Step 4 was skipped.
