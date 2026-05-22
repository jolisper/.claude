# Spec: Git Worktree Skill Family

**Date:** 2026-05-19
**Status:** Implemented

---

## Summary

Two new skills to complete the worktree workflow in the git family:

| Skill | Purpose |
|-------|---------|
| `git-worktree` | Full worktree lifecycle: add, list, remove, prune, close — context-aware | ✅ Implemented |
| `git-merge` | Merge a branch into the current branch, strictly `--ff-only` | ✅ Implemented |

The two skills are complementary but independently useful. `git-worktree close`
is the primary composition point — it delegates to `git-merge`'s protocol before
removing the worktree and its branch.

---

## Context

The existing git family covers the full individual-branch workflow:
branch → commit → push → rebase → PR. What's missing is the **worktree loop**:
creating an isolated checkout, working in it, and closing it out when done.

A worktree lets you check out a second branch in a separate directory without
stashing or switching — useful for reviewing a PR while keeping your current
work intact, or running a long build on main while developing on a feature branch.

`git-worktree` is a self-contained skill with no dependency on any external tool.
It owns the full lifecycle using only standard git porcelain commands:

1. **Creation** — add a new worktree for a branch (new or existing), with a
   consistent path convention.
2. **Visibility** — list all active worktrees with branch, path, and dirty state.
3. **Close-out** — merge + branch delete + worktree remove in one guided flow.
4. **Cleanup** — prune stale worktree records.

---

## Design Decisions

### D1 — `git-worktree` owns the full lifecycle, including `add`

The skill is self-contained. It does not delegate creation to any external tool.
`add` creates the worktree at a predictable path derived from the repo name and
branch name (see D2). Users running any terminal or editor get the same behavior.

### D2 — Worktree path convention: sibling directory

New worktrees are placed as siblings of the main repo directory:

```
<repo-parent>/<repo-name>-<branch>/
```

Example: repo at `~/projects/myapp`, branch `feat/auth`:

```
~/projects/myapp-feat-auth/
```

The branch name is slugified (slashes → hyphens). This convention:
- Keeps worktrees out of the repo directory (no `.gitignore` pollution)
- Is predictable and reversible from any context
- Requires no configuration

The user may override with an explicit path argument: `add <branch> <path>`.

### D3 — `git-merge` is strictly `--ff-only`; rebase is the only resolution for divergence

A worktree branch must be transparent to main: main's history should look as if
the work happened inline. `--ff-only` enforces this — a merge commit would break
linear history and expose the worktree's parallel existence.

If a fast-forward is not possible (main moved on while the worktree was active),
the only correct resolution is to rebase the worktree branch onto the new main
and retry. There is no `--no-ff` flag or merge-commit escape hatch. The skill
stops and directs the user to `/git-rebase` before retrying.

### D4 — `git-worktree close` is the primary composition point

`git-worktree close <branch>` chains merge → branch delete → worktree remove
in a single guided flow. It reads and follows `git-merge`'s SKILL.md protocol
for the merge step rather than duplicating logic — same pattern as
`git-commit-push` delegating to `git-commit` and `git-push`.

### D5 — Each step in `close` is individually confirmed

The close-out sequence is irreversible. The skill asks before each destructive
step (merge, branch delete, worktree remove). A failure at any step stops the
sequence and leaves everything in a consistent state.

### D6 — The skill detects execution context and adapts

At the start of every invocation the skill determines its context by running
`git rev-parse --git-dir`. If the output path contains `/worktrees/`, the
session is inside a worktree (`IN_WORKTREE=true`); otherwise it is running
from the main repo (`IN_WORKTREE=false`).

When `IN_WORKTREE=true`, the skill also derives the main repo root:

```
COMMON_DIR = git rev-parse --git-common-dir   # e.g. /path/to/repo/.git
MAIN_REPO  = parent directory of COMMON_DIR   # e.g. /path/to/repo
```

This path is used for `git -C <MAIN_REPO>` operations when the skill must act
on the main repo from within a worktree — a justified exception to the
no-`git -C` rule, since the intent is explicitly to target a different checkout.

Adaptations per subcommand:

| Subcommand | In main repo | In a worktree |
|---|---|---|
| `list` | normal | normal |
| `prune` | normal | normal |
| `add` | normal | normal |
| `remove <branch>` | normal | refuses if `<branch>` == current branch |
| `close` (no args) | asks which branch | defaults to current branch |
| `close <branch>` where `<branch>` ≠ current | normal | normal |
| `close <branch>` where `<branch>` == current | normal | "closing from inside" mode (see below) |

### D7 — "Closing from inside" uses `git -C <MAIN_REPO>`

When `close` targets the current branch and `IN_WORKTREE=true`, git imposes
three constraints: the current branch cannot be deleted, the current directory
cannot be removed, and `main` is checked out in a different worktree so a
direct merge is not possible here.

The skill handles this by running all three destructive steps — merge, branch
delete, and worktree remove — via `git -C <MAIN_REPO>`, which operates on the
main repo checkout. Before the worktree removal step the skill warns: "Removing
this worktree will delete your current working directory."

This is the one place where `git -C` is permitted; the reason is documented
inline in the skill and in this spec.

### D8 — `git-merge` needs no conflict handling

`git merge --ff-only` either moves the HEAD pointer or exits non-zero — it never
produces a conflict state, because no content merging occurs. The conflict
resolution protocol is therefore not needed in `git-merge`.

The shared reference doc originally planned here (`git-rebase/references/conflict-resolution.md`)
remains a valid future refactor to consolidate the duplicated conflict protocol
in `git-pull` and `git-rebase`, but it is not a prerequisite for this skill family.

### D9 — `close` always reports worktree removal status explicitly

When no worktree is found for the target branch, the skill says so: "No worktree
found for `<TARGET>` — skipping removal." Silent skips hide information the user
may need (e.g. they expected a worktree to exist).

### D10 — Worktree branches are always local; no remote push check

Worktree branches follow the lifecycle: create from main → commit → merge into
main → close. They are never pushed to a remote. The `close` subcommand therefore
performs no unpushed-commits check — it would always false-positive on local-only
branches. The `--force` flag that previously bypassed this check has been removed.

### D11 — `git-merge` is standalone and strictly `--ff-only` in all contexts

`git-merge` is not scoped to worktree close-outs. It is the single merge
primitive for the entire git skill family — worktree or not — and it enforces
`--ff-only` unconditionally. This is a global linear-history policy, not a
worktree-specific constraint.

If a merge commit is intentional (release branch, external integration), the
user runs `git merge` directly in the terminal. The skill family does not
support that workflow.

### D12 — `add` records the base branch as upstream

When creating a new worktree branch, the skill captures the current branch
(`BASE_BRANCH`) before creating the worktree, then sets it as the new branch's
local upstream: `git branch --set-upstream-to <BASE_BRANCH> <branch>`. This
records the intended merge target without external metadata, enabling `list`,
`prune`, and `close` to resolve the correct divergence reference and merge
target automatically.

### D13 — Divergence is computed per-branch against the upstream, with fallback to main

`list` and `prune` determine each branch's divergence reference from its local
upstream (`git branch --format '%(upstream:short)' --list <branch>`). If no
upstream is set (branch created outside this skill), the fallback is
`MAIN_BRANCH` and a `vs main` marker is appended to the status so the user can
see the fallback was applied. This makes divergence semantically accurate: a
branch tracking `develop` shows ahead/synced relative to `develop`, not `main`.

### D14 — Session detection uses agent process filtering

A worktree is considered active only when a known agent process has its cwd in
that directory. Detection uses:

```
lsof -a -d cwd -c claude -c cursor -c windsurf -c codex -c aider -c opencode -c gemini +d <path>
```

Shells (`zsh`, `bash`, etc.) are excluded — a terminal sitting in the directory
is not a meaningful active session (its cwd is inherited at launch and may be
stale). Agent processes directly indicate intentional work in that directory.
Active-session worktrees are flagged with `, session` in `list` and blocked from
removal in `prune`.

### D15 — `close` detects merge target from upstream

Before merging, `close` reads the target branch's local upstream to determine
`MERGE_TARGET`. If an upstream is set, it is used silently. If not, the user is
prompted to confirm the `main`/`master` fallback or choose a different target.
This generalizes `close` to support feature-branch workflows where the merge
target is not always `main`.

### D16 — `close` pre-flights uncommitted changes before any destructive step

Before the merge step, `close` checks for uncommitted changes in the target
worktree. In closing-from-inside mode, the user can commit via `git-commit
--auto` and continue. In normal mode, the user is directed to switch to the
worktree and commit first. This prevents data loss from close-outs that start
with a dirty worktree.

---

## Skill: `git-worktree`

**Invocation:** `/git-worktree [add <branch> [path] | list | remove <branch> | prune | close [<branch>]]`
**Argument hint:** `[add <branch> | list | remove <branch> | prune | close [<branch>]]`
**Model-invocable:** `false`
**disable-model-invocation:** `true`
**Allowed tools:**
```
Bash(git worktree:*)
Bash(git rev-parse:*)
Bash(git branch:*)
Bash(git log:*)
Bash(git status:*)
Bash(git merge:*)
Bash(git -C:*)
Bash(lsof:*)
Bash(printf:*)
Read
```
(`close` additionally inherits the allowed tools from `git-merge` for the merge step.)

**Context detection (runs before every subcommand):**

```
git rev-parse --git-dir
```

If the output contains `/worktrees/`: `IN_WORKTREE=true`.
Also run `git rev-parse --git-common-dir` and strip the trailing `/.git`
component to get `MAIN_REPO`. Both values are available to all subcommand steps.

---

### Subcommand: `add <branch> [path]`

Creates a new worktree. `<branch>` may be an existing local branch or a new
branch name. An optional `<path>` overrides the default location.

**Step 1 — Resolve branch**

If `<branch>` matches an existing local branch: use it as-is (checkout existing).
Otherwise: treat it as a new branch name and create it from the current HEAD.

Validate the branch name against the Conventional Branch spec (read
`~/.claude/skills/git-new-branch/references/conventional-branch-spec.md`).
On violation: list each rule broken and ask for a corrected name.

**Step 2 — Resolve path**

If `<path>` is provided: use it directly.

Otherwise: derive from the repo name and branch name:
1. `git rev-parse --show-toplevel` → `<repo-root>`
2. Extract `<repo-name>` from the last path component of `<repo-root>`.
3. Slugify `<branch>`: replace `/` with `-`, lowercase.
4. Path = `<repo-root>/../<repo-name>-<slugified-branch>`

Show the resolved path and ask: `Create worktree at <path>? (y/n)`

**Step 3 — Create**

For new branches only: capture `BASE_BRANCH` = current branch before creating the worktree.

- Existing branch: `git worktree add <path> <branch>`
- New branch: `git worktree add -b <branch> <path>`, then
  `git -C <path> branch --set-upstream-to <BASE_BRANCH> <branch>`

This sets the local upstream so `list`, `prune`, and `close` can resolve the correct
divergence reference and merge target automatically (D12).

**Step 4 — Confirm**

```
Worktree created:
  Branch: <branch>
  Path:   <path>
```

---

### Subcommand: `list` (default when no args)

1. Run `git worktree list --porcelain`.
2. Parse each block: extract `worktree <path>`, `HEAD <sha>`, and
   `branch <refname>` (or `detached`).
3. Determine `MAIN_BRANCH`: `git branch --list main` → `main`, else `master`.
4. For each worktree: `git -C <path> status --short` → dirty / clean.
5. For each non-main worktree (skip detached HEAD):
   - `git branch --format '%(upstream:short)' --list <branch>` → if non-empty: `DIVERGE_REF=<upstream>`, no fallback marker.
   - Otherwise: `DIVERGE_REF=<MAIN_BRANCH>`, set fallback marker.
   - `git log <DIVERGE_REF>..<branch> --oneline` → non-empty: **ahead**; empty: **synced**.
6. For each worktree: run session detection — `lsof -a -d cwd -c claude -c cursor -c windsurf -c codex -c aider -c opencode -c gemini +d <path>` — non-empty stdout: session active.
7. Display with `printf` for aligned columns (compute column widths from actual data):

   ```
   Worktrees:

     * main           ~/.claude                                cb13978  (dirty, session)
       bolson-ravine  ~/.warp/worktrees/.claude/bolson-ravine  3caa860  (clean, ahead vs main, session)
       feat/auth      ~/projects/myapp-feat-auth               a3f91d2  (clean, ahead)
   ```

   `*` marks the current worktree. Replace `$HOME` with `~`. Show first 7 SHA chars.
   - Main worktree: `dirty` or `clean`; no divergence label; append `, session` if active.
   - Non-main: `dirty/clean, ahead/synced`; if fallback was used, append ` vs <MAIN_BRANCH>` after the divergence label; append `, session` if active.
   - Detached HEAD: `detached HEAD`; append `, session` if active.

---

### Subcommand: `remove <branch>`

Removes the worktree for the named branch.

1. Run `git worktree list --porcelain` to find the path for `<branch>`.
   If not found: "No worktree found for branch `<branch>`." Stop.
2. If `IN_WORKTREE=true` and `<branch>` matches the current branch:
   "You are inside this worktree. Use `close` to merge and remove it, or
   switch to another worktree and run `remove` from there." Stop.
3. Run `git -C <path> status --short`. If non-empty:
   ```
   The worktree at <path> has uncommitted changes:
   <status output>
   Remove anyway? (y/n)
   ```
   Stop if not confirmed.
4. Run `git worktree remove <path>`.
5. Confirm: `Worktree removed: <path>`

---

### Subcommand: `prune`

**Step 1 — Remove stale records:** `git worktree prune --verbose`.

**Step 2 — Detect prunable worktrees:**
For each non-main worktree, compute dirty/clean and ahead/synced using the same upstream
divergence logic as `list` (upstream if set, fallback to MAIN_BRANCH).
A worktree is prunable when it is **synced** (no commits ahead of its divergence ref).

Split synced candidates into groups:
- **clean + synced** — safe to remove
- **dirty + synced** — warn before removing (uncommitted work will be lost)
- **blocked** — active agent session detected (excluded from removal regardless of state)

Skip the current worktree if `IN_WORKTREE=true`. Show candidates grouped and ask:

| Groups present | Menu |
|---|---|
| clean+synced only | (a) Remove all / (b) Cancel |
| dirty+synced only | (a) Remove anyway / (b) Cancel |
| both | (a) Remove clean only / (b) Remove all including dirty / (c) Cancel |

Blocked worktrees are shown but never offered for removal. Remove approved worktrees one
by one; on error continue to the next. Then `git worktree prune`.

---

### Subcommand: `close [<branch>]`

Full close-out: merge → branch delete → worktree remove. Stops on any failure.
Context-aware: behavior differs depending on whether the session is inside the
worktree being closed.

**Step 1 — Pre-flight**

1. Run `git rev-parse --abbrev-ref HEAD` — note current branch (`CURRENT`).
2. Resolve the target branch (`TARGET`):
   - If `$ARGUMENTS` supplies a branch name: use it.
   - If no branch name and `CURRENT` is not main/master: default to `CURRENT`.
     Tell the user: "Closing current branch: `<CURRENT>`."
   - If no branch name and `CURRENT` is main/master: ask "Which branch do you
     want to close out?"
3. Verify target exists: `git branch --list <TARGET>`. Stop if not found.
4. Detect `MERGE_TARGET` (D15):
   - `git branch --format '%(upstream:short)' --list <TARGET>` → if non-empty, use it silently.
   - Otherwise: `git branch --list main` → non-empty: `FALLBACK=main`, else `FALLBACK=master`. Show:
     ```
     No upstream set for `<TARGET>` — defaulting merge target to `<FALLBACK>`.
     (a) Merge into <FALLBACK>
     (b) Choose a different target
     (c) Cancel
     ```
     On (b): ask which branch, use the answer as `MERGE_TARGET`. Stop on (c).
5. Determine execution mode:
   - `CLOSING_FROM_INSIDE = (IN_WORKTREE=true AND TARGET == CURRENT)`
6. Dirty check (D16): find the worktree path for `TARGET` and run `git -C <path> status --short`.
   If non-empty:
   - *Closing-from-inside mode:* offer `(a) Commit changes and continue / (b) Proceed without committing (changes will be lost) / (c) Cancel`. On (a): follow `git-commit --auto` protocol, then continue. Stop on (c).
   - *Normal mode:* direct the user to switch to the worktree and commit first. Offer `(a) Proceed anyway (changes will be lost) / (b) Cancel`. Stop on (b).

**Step 2 — Merge**

*Normal mode* (`CLOSING_FROM_INSIDE=false`):

Verify current branch is `MERGE_TARGET`; if not, stop: "Switch to `<MERGE_TARGET>` before closing out."
Read `~/.claude/skills/git-merge/SKILL.md` and follow its full protocol to merge `<TARGET>` into `MERGE_TARGET`.

*Closing-from-inside mode* (`CLOSING_FROM_INSIDE=true`):

1. Run `git -C <MAIN_REPO> rev-parse --abbrev-ref HEAD` — must equal `MERGE_TARGET`.
   If not: "The main repo is on `<other>`, not `<MERGE_TARGET>`. Switch it first." Stop.
2. Run `git -C <MAIN_REPO> log <MERGE_TARGET>..<TARGET> --oneline` — show commits.
3. Ask:
   ```
   Merge <TARGET> → <MERGE_TARGET>  [fast-forward]
   (a) Merge
   (b) Cancel
   ```
4. On (a): `git -C <MAIN_REPO> merge --ff-only <TARGET>`. On non-zero exit: show error and stop.

**Step 3 — Delete branch**

```
Delete branch <TARGET>?
(a) Delete
(b) Cancel
```

*Normal mode:* `git branch -d <TARGET>`
*Closing-from-inside mode:* `git -C <MAIN_REPO> branch -d <TARGET>`

If the delete fails, surface the error and stop — do not force-delete.

**Step 4 — Remove worktree**

Run `git worktree list --porcelain` (or `git -C <MAIN_REPO> worktree list --porcelain`
in closing-from-inside mode) to find the path for `<TARGET>`.
If no worktree found, skip and say "No worktree found for `<TARGET>` — skipping removal."

*Normal mode:*
```
Remove worktree at <path>?
(a) Remove
(b) Cancel
```
On (a): `git worktree remove <path>`, then `git worktree prune`.

*Closing-from-inside mode:*
```
⚠ Removing this worktree will delete your current working directory (<path>).
(a) Remove
(b) Cancel
```
On (a): `git -C <MAIN_REPO> worktree remove <path>`, then `git -C <MAIN_REPO> worktree prune`.

**Step 5 — Summary**

```
Close-out complete:
  ✓ Merged <TARGET> into <MERGE_TARGET> (fast-forward)
  ✓ Deleted branch <TARGET>
  ✓ Removed worktree <path>
```

---

## Skill: `git-merge`

**Invocation:** `/git-merge [<branch>]`
**Argument hint:** `[<branch>]`

**Model-invocable:** `false`
**disable-model-invocation:** `true`
**Allowed tools:**
```
Bash(git rev-parse:*)
Bash(git log:*)
Bash(git merge:*)
Bash(git status:*)
Bash(git diff:*)
Bash(git branch:*)
Bash(git add:*)
Bash(git checkout:*)
Bash(python3:*)
Read
Edit
```

---

### Protocol

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command
separately with no path arguments — rely on the shell's current working
directory.

**Step 1 — Resolve source branch**

If `$ARGUMENTS` contains a branch name, use it. Otherwise:
1. Run `git branch` to list local branches.
2. Filter out the current branch.
3. Present a numbered list and ask: "Which branch do you want to merge in?"

**Step 2 — Pre-flight**

1. `git rev-parse --abbrev-ref HEAD` — note `TARGET` (current branch).
2. `git status --short` — if non-empty, warn about dirty tree:
   ```
   You have uncommitted changes. Merge anyway? (y/n)
   ```
   Stop if not confirmed.
3. `git log <TARGET>..<source> --oneline` — commits in source not in TARGET.
   If empty: "Branch `<source>` has no new commits to merge." Stop.

**Step 3 — Fast-forward check**

Run `git merge-base HEAD <source>` to get the common ancestor.
Run `git rev-parse HEAD` and `git rev-parse <source>`.

- `merge-base == HEAD` → fast-forward is possible. Proceed to Step 4.
- `merge-base == <source>` → TARGET is already ahead of source. Say so and stop.
- Otherwise → histories have diverged; fast-forward is not possible.
  ```
  ✗ Cannot fast-forward: <source> has diverged from <TARGET>.
    Rebase <source> onto <TARGET> first, then retry.
    Run: /git-rebase
  ```
  Stop.

**Step 4 — Confirm and merge**

Show the commits to be merged and ask:

```
Merge <source> → <TARGET>  [fast-forward]
  abc1234  feat: add login flow
  def5678  fix: token expiry

Proceed? (y/n)
```

On yes: `git merge --ff-only <source>`

**Step 5 — Interpret the result**

- **Success** — show: `Merged <source> into <TARGET> (fast-forward).`
- **Conflict** — read `~/.claude/skills/git-rebase/references/conflict-resolution.md`
  and follow the guided conflict flow defined there. After all conflicts are
  resolved, run `git commit`.
- **Error** — show stderr and explain the likely cause.

**Step 6 — Post-merge**

Show `git log ORIG_HEAD..HEAD --oneline` to confirm what was integrated.

---

## Skill Interaction

```
/git-worktree close <branch>
  └─ reads git-merge SKILL.md → follows full git-merge protocol
  └─ git branch -d <branch>
  └─ git worktree remove <path>
  └─ git worktree prune
```

`git-merge` is callable standalone with no dependency on `git-worktree`.
The delegation is one-directional.

---

## Implementation Order

1. ~~**Extract conflict-resolution reference**~~ — Superseded. `git merge --ff-only`
   cannot produce conflicts (it moves a pointer or fails — no content merging occurs),
   so `git-merge` needs no conflict handling. D8 remains valid as a future refactor
   of `git-pull` and `git-rebase` to consolidate their duplicated protocol, but it
   is off the critical path for this family.
2. ✅ **`git-merge`** — implemented at `~/.claude/skills/git-merge/SKILL.md`.
3. ✅ **`git-worktree`** — implemented at `~/.claude/skills/git-worktree/SKILL.md`.

---

## Open Questions

All resolved.

~~1. **`close` from inside the target worktree**~~ — Resolved (D7). The skill
detects `CLOSING_FROM_INSIDE=true` and executes merge, branch delete, and
worktree remove via `git -C <MAIN_REPO>`. A warning is shown before removal
since it deletes the current working directory.

~~2. **`--merge-commit` vs `--no-ff`**~~ — Superseded. No opt-in flag exists.
`git-merge` is strictly `--ff-only`; diverged histories require a rebase (D3).

~~3. **Conflict resolution cross-dependency**~~ — Superseded (D8). `--ff-only`
cannot produce conflicts, so `git-merge` needs no conflict handling at all.
The shared reference doc remains a future refactor for `git-pull`/`git-rebase`.

~~4. **`close` with no worktree**~~ — Resolved (D9). Always explicit: "No
worktree found for `<TARGET>` — skipping removal." No silent skips.

~~5. **Push enforcement before close**~~ — Superseded (D10). Worktree branches
are always local-only; no push check is performed.
