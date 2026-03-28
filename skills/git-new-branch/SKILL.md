---
name: git-new-branch
description: >
  Use this skill when the user wants to create a new branch from the latest
  main/master. Invoke for requests like "new branch", "create branch",
  "start a new feature branch", or "branch off main". Updates the main
  development branch first, then creates and checks out the new branch.
  Accepts an optional branch name following the Conventional Branch spec
  (e.g. feat/add-login, fix/issue-42-header).
disable-model-invocation: true
argument-hint: "feat/branch-description"
allowed-tools: Bash(git:*)
---

Update main/master and create a new branch from it. Branch names follow the Conventional Branch spec: `<type>/<description>`.

## Phase 1 — Resolve branch name

**If `$ARGUMENTS` is non-empty**, use it as the full branch name and jump to **→ Validate**.

**If `$ARGUMENTS` is empty**, run the interactive flow below.

### Step 1 — Type

Show this menu and wait for the user's choice (accept number or keyword):

```
Select branch type:
1. feat     — new feature
2. fix      — bug correction
3. hotfix   — critical urgent fix
4. release  — release preparation  (e.g. release/v1.2.0)
5. chore    — non-code task (docs, deps, config)

(Aliases feature/ and bugfix/ are also accepted as arguments.)
```

### Step 2 — Description

Ask: `Description (lowercase, hyphens only — e.g. add-login, issue-42-header):`

Process the user's reply:

- **Spec-compliant** (lowercase a–z/0–9/hyphens, no leading/trailing/consecutive hyphens): assemble `<type>/<description>` and jump to **→ Validate**.
- **Colloquial** (contains spaces, mixed case, or informal phrasing): read `~/.claude/skills/git-new-branch/references/conventional-branch-spec.md`, then use the translation patterns and examples there to interpret the intent and present **4 spec-compliant description options** numbered for selection:
  - Options 1–2: **3-word kebab names** (e.g. `add-login-flow`, `fix-auth-token`)
  - Options 3–4: **4-word kebab names** (e.g. `add-user-login-flow`, `fix-auth-token-refresh`)
  Ask the user to pick one (1–4) or type their own. Re-process until compliant.
- **Violates a specific rule**: state which rule was broken in one line, ask them to re-enter.

### → Validate

Check the full branch name against the Conventional Branch spec:

| Rule | Requirement |
|---|---|
| Format | Exactly one `/` separating type and description |
| Type | One of: `feat`, `feature`, `bugfix`, `fix`, `hotfix`, `release`, `chore` |
| Characters | Lowercase a–z, digits 0–9, hyphens. Dots allowed in `<description>` for `release/` only. |
| Hyphens | No consecutive `--`, no leading or trailing hyphens in either segment |
| Description | Non-empty |

If **any rule fails**: list each violation with a one-line explanation, then ask the user for a corrected name. Re-validate. Repeat until all rules pass.

## Phase 2 — Pre-flight check

Run `git status --short`. If the output is non-empty (dirty working tree), warn the user:

```
Warning: you have uncommitted changes. Checking out '<main-branch>' may affect your working tree.
Proceed anyway? (y/n)
```

Stop if the user answers anything other than `y`.

## Phase 3 — Update main branch

Run `git branch --list main`. If output is non-empty, use `main`. Otherwise run `git branch --list master` — if non-empty, use `master`. If neither exists, ask the user which local branch to update from.

Check out the main branch with `git checkout <main-branch>`.

Pull the latest changes with `git pull`.

If the pull fails, stop and report the error (include the git error output). Tell the user to check: network connectivity, upstream remote config (`git remote -v`), or whether a rebase/merge is already in progress. Do not proceed to Phase 4.

## Phase 4 — Create the branch

Run `git checkout -b <validated-branch-name>`.

Report: `Branch '<name>' created and checked out from '<main-branch>'.`
