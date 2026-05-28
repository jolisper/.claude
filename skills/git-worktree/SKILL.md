---
name: git-worktree
description: >
  Use this skill to manage git worktrees — add, list, remove, prune, and close
  out a worktree branch. Invoke for requests like "new worktree for <branch>",
  "list my worktrees", "close this worktree", "remove worktree X", or "prune
  stale worktrees". Context-aware: adapts behavior when invoked from inside a
  worktree.
disable-model-invocation: true
argument-hint: "[add <branch> [path] | list | remove <branch> | prune | close [<branch>]]"
allowed-tools: Bash(git worktree:*) Bash(git rev-parse:*) Bash(git branch:*) Bash(git log:*) Bash(git status:*) Bash(git merge:*) Bash(git -C:*) Bash(lsof:*) Bash(printf:*) Bash(bash:*) Read
skills: git-merge, git-commit
when_to_use: >
  Invoke when the user wants to add, list, remove, prune, or close out a git
  worktree, or asks about managing multiple checkouts of a repository.
effort: high
---

Full worktree lifecycle management. Enforces a linear-history policy: `close`
merges via fast-forward only.

**Rule**: Never use `&&`, `||`, or pipes. One command per Bash call.
`git -C <path>` is explicitly permitted for targeting specific worktrees.

**Rule**: Never call `AskUserQuestion` — output text menus directly and wait for the user to type a response.

**Rule**: `lsof` on macOS exits with code 1 even when it finds results (permission
errors from other users' processes). Treat exit code 1 as normal — check only
whether stdout is non-empty to determine if a session is active.

**Session detection**: a worktree is considered active only when a known agent
process has its cwd there. Use this exact command:
`lsof -a -d cwd -c claude -c cursor -c windsurf -c codex -c aider -c opencode -c gemini +d <path>`

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

Otherwise:

1. `git rev-parse --show-toplevel` → `<repo-root>`
2. Last path component of `<repo-root>` → `<repo-name>`
3. Slugify `<branch>`: replace `/` with `-`, lowercase → `<slug>`

**2a. Read config** — run `bash ~/.claude/skills/git-worktree/scripts/resolve-worktree-path.sh`:
- Exit 1 → report the error message from stderr and stop.
- Exit 0, stdout contains `status=done path=<dir>` → extract `<dir>` as `<BASE>`; derive path: `<BASE>/<repo-name>-<slug>`
- Exit 0, empty stdout → fall through to 2b.

**2b. Default path** (no config or `worktrees_path` absent/empty):
- Path = `<repo-root>/../<repo-name>-<slug>`

Show the resolved path and confirm:
```
Create worktree at <path>?
(a) Yes
(b) Cancel
```
Stop on (b).

**Step 3 — Create**

For new branches only: capture `BASE_BRANCH` = `git rev-parse --abbrev-ref HEAD`
before creating the worktree.

- Existing branch: `git worktree add <path> <branch>`
- New branch: `git worktree add -b <branch> <path>`, then
  `git -C <path> branch --set-upstream-to <BASE_BRANCH> <branch>`

On non-zero exit of any command: show the git error and stop.

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
5. For each non-main worktree (skip detached HEAD):
   - `git branch --format '%(upstream:short)' --list <branch>` → if non-empty: `DIVERGE_REF=<upstream>`, no fallback marker.
   - Otherwise: `DIVERGE_REF=<MAIN_BRANCH>`, set fallback marker.
   - `git log <DIVERGE_REF>..<branch> --oneline` — non-empty: ahead; empty: synced.
6. For each worktree: run the session detection command (see Rules) with `<path>` — non-empty stdout: session active.

Display with aligned columns. Compute column widths from the actual data:
- **W1** = longest branch name across all worktrees
- **W2** = longest path across all worktrees (after replacing `$HOME` with `~`)

Replace `$HOME` with `~`. Show first 7 sha chars. Build `<status>` per row:
- Main worktree: `dirty` or `clean`; no divergence label; append `, session` if active.
- Non-main worktrees: `dirty/clean, ahead/synced`; if fallback was used, append ` vs <MAIN_BRANCH>` after the divergence label; append `, session` if active.
- Detached HEAD: `detached HEAD`; append `, session` if active.

Emit each row with `printf`, using `%-W1s` and `%-W2s` to pad columns exactly:
- Non-current: `printf "    %-W1s  %-W2s  %s  (%s)\n" "<branch>" "<path>" "<sha7>" "<status>"`
- Current:     `printf "  * %-W1s  %-W2s  %s  (%s)\n" "<branch>" "<path>" "<sha7>" "<status>"`

Example output:
```
Worktrees:

    main           ~/.claude                                cb13978  (dirty, session)
  * bolson-ravine  ~/.warp/worktrees/.claude/bolson-ravine  3caa860  (clean, ahead vs main, session)
    feat/auth      ~/projects/myapp-feat-auth               a3f91d2  (clean, ahead)
```

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
3. For each:
   - `git branch --format '%(upstream:short)' --list <branch>` → if non-empty: `DIVERGE_REF=<upstream>`, no fallback marker.
   - Otherwise: `DIVERGE_REF=<MAIN_BRANCH>`, set fallback marker.
   - `git log <DIVERGE_REF>..<branch> --oneline`. Empty → synced.
4. If no synced worktrees: stop.
5. For each synced worktree: `git -C <path> status --short`.
   - Empty → **clean + synced**
   - Non-empty → **dirty + synced**
6. For each synced worktree: run the session detection command (see Rules) with `<path>`.
   - Non-empty stdout → **blocked** (active session — move out of the prunable candidates regardless of dirty/clean state).
7. If `IN_WORKTREE=true` and the current branch is synced, mark it "(current — skipping)"
   and exclude it. If all candidates were skipped or blocked: stop.
8. Show candidates grouped (omit a group if empty). When fallback was used for a branch,
   append `vs <MAIN_BRANCH>` after the divergence label:
   ```
   Prunable worktrees:

     <branch>  <path>  (clean, synced)            ← upstream set
     <branch>  <path>  (clean, synced vs main)    ← no upstream, fallback applied

   Prunable with uncommitted changes:

     <branch>  <path>  (dirty, synced vs main)

   Blocked — active session:

     <branch>  <path>  (clean, synced, session)
   ```
9. Ask based on which prunable groups are present (blocked group is never offered for removal):

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

   *Both clean+synced and dirty+synced:*
   ```
   (a) Remove clean only
   (b) Remove all (including dirty)
   (c) Cancel
   ```

   Stop on Cancel.

10. For each approved worktree: `git worktree remove <path>`.
    On non-zero exit: show the error and continue to the next — do not abort the batch.
11. `git worktree prune`.
12. "Removed N worktree(s)." If any were blocked: "N worktree(s) skipped — active session detected."

---

## close

Full close-out: merge → worktree remove → branch delete (closing-from-inside), or merge → branch delete → worktree remove (normal). Stops on any failure.
No step auto-rolls back a previous one.

**Step 1 — Pre-flight**

Check for in-progress git operations:
- `git rev-parse MERGE_HEAD` — if exit 0: "A merge is in progress — resolve it before closing out." Stop.
- `git rev-parse CHERRY_PICK_HEAD` — if exit 0: "A cherry-pick is in progress — resolve it before closing out." Stop.
- `git rev-parse REBASE_HEAD` — if exit 0: "A rebase is in progress — resolve it before closing out." Stop.

1. `git rev-parse --abbrev-ref HEAD` → `CURRENT`.
2. Resolve `TARGET`:
   - Branch name after `close` in `$ARGUMENTS` → use it.
   - No branch name and `CURRENT` is not `main`/`master` → use `CURRENT`.
     Tell the user: "Closing current branch: `<CURRENT>`."
   - No branch name and `CURRENT` is `main`/`master` → ask:
     "Which branch do you want to close out?"
3. `git branch --list <TARGET>` — empty: "Branch `<TARGET>` not found." Stop.
4. Detect `MERGE_TARGET`:
   - `git branch --format '%(upstream:short)' --list <TARGET>` → if non-empty, use it silently.
   - Otherwise: `git branch --list main` → non-empty: `FALLBACK=main`, else `FALLBACK=master`.
     Show:
     ```
     No upstream set for `<TARGET>` — defaulting merge target to `<FALLBACK>`.
     (a) Merge into <FALLBACK>
     (b) Choose a different target
     (c) Cancel
     ```
     On (b): ask "Merge into which branch?" and use the answer as `MERGE_TARGET`.
     Stop on (c).
5. Set `CLOSING_FROM_INSIDE = (IN_WORKTREE=true AND TARGET == CURRENT)`.
6. Dirty check — find the worktree path for `TARGET`:
   *Normal mode:* `git worktree list --porcelain` → find block for `refs/heads/<TARGET>` → extract path.
   *Closing-from-inside mode:* path = current working directory (`git rev-parse --show-toplevel`).
   Run `git -C <path> status --short`. If non-empty:

   *Closing-from-inside mode:*
   ```
   The worktree has uncommitted changes:
   <status lines>

   (a) Commit changes and continue
   (b) Proceed without committing (changes will be lost)
   (c) Cancel
   ```
   On (a): Read `~/.claude/skills/git-commit/SKILL.md` and follow its full protocol
   with `--auto`. After the commit completes, continue to Step 2.
   (git-commit uses only git Bash commands and Read; all required tools are covered by this skill's allowed-tools.)
   Stop on (c).

   *Normal mode:*
   ```
   The worktree at <path> has uncommitted changes:
   <status lines>

   Switch to that worktree and commit before closing out.
   (a) Proceed anyway (changes will be lost)
   (b) Cancel
   ```
   Stop on (b).

**Step 2 — Merge**

*Normal mode* (`CLOSING_FROM_INSIDE=false`):

Run `git rev-parse --abbrev-ref HEAD`. If not `MERGE_TARGET`:
"Switch to `<MERGE_TARGET>` before closing out." Stop.

Read `~/.claude/skills/git-merge/SKILL.md` and follow its full protocol with
`<TARGET>` as the source branch. (git-merge uses only git Bash commands and Read;
all required tools are covered by this skill's allowed-tools.) If the merge fails
or the user cancels: stop. Do not proceed to Step 3.

*Closing-from-inside mode* (`CLOSING_FROM_INSIDE=true`):

1. `git -C <MAIN_REPO> rev-parse --abbrev-ref HEAD` — must equal `MERGE_TARGET`.
   If not: "The main repo is on `<other>`, not `<MERGE_TARGET>`. Switch it first." Stop.
2. `git -C <MAIN_REPO> log <MERGE_TARGET>..<TARGET> --oneline` — show commits.
3. `git -C <MAIN_REPO> merge --ff-only <TARGET>`.
   On non-zero exit: show the error and stop.

**Step 3 — Remove worktree** *(closing-from-inside mode only — git requires worktree removal before the branch can be deleted)*

*Normal mode:* skip to Step 4.

*Closing-from-inside mode:*

`git -C <MAIN_REPO> worktree list --porcelain` — find the block for `refs/heads/<TARGET>`. If not found:
"No worktree found for `<TARGET>` — skipping removal." Skip to Step 4.

```
⚠ Removing this worktree will delete your current working directory (<path>).
(a) Remove
(b) Cancel
```

Stop on (b).

Run `git -C <MAIN_REPO> worktree remove <path>`.
Run `git -C <MAIN_REPO> worktree prune`.

On non-zero exit: show the error and stop.

**Step 4 — Delete branch**

```
Delete branch <TARGET>?
(a) Delete
(b) Cancel
```
Stop on (b).

*Normal mode:* `git branch -d <TARGET>`
*Closing-from-inside mode:* `git -C <MAIN_REPO> branch -d <TARGET>`

On failure: show the error and stop — do not force-delete.

**Step 5 — Remove worktree** *(normal mode only)*

*Closing-from-inside mode:* skip to Step 6 (worktree already removed in Step 3).

`git worktree list --porcelain` — find the block for `refs/heads/<TARGET>`. If not found:
"No worktree found for `<TARGET>` — skipping removal." Skip to Step 6.

```
Remove worktree at <path>?
(a) Remove
(b) Cancel
```

Stop on (b).

Run `git worktree remove <path>`.
Run `git worktree prune`.

On non-zero exit: show the error and stop.

**Step 6 — Summary**

```
Close-out complete:
  ✓ Merged <TARGET> into <MERGE_TARGET> (fast-forward)
  ✓ Deleted branch <TARGET>
  ✓ Removed worktree <path>
```

Omit the worktree line if it was skipped.
