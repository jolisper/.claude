---
name: git-new-branch
description: >
  Use this skill when the user wants to create a new branch from the latest
  main/master. Invoke for requests like "new branch", "create branch",
  "start a new feature branch", or "branch off main". Updates the main
  development branch first, then creates and checks out the new branch.
  Accepts an optional branch name following the Conventional Branch spec
  (e.g. feat/add-login, fix/issue-42-header). Auto mode is on by default:
  with no branch name given, it infers a representative type/description
  from context instead of prompting (pass --no-auto for the interactive menus).
disable-model-invocation: true
argument-hint: "[feat/branch-description | --no-auto]"
allowed-tools: Bash(git:*)
---

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

Update main/master and create a new branch from it. Branch names follow the Conventional Branch spec: `<type>/<description>`.

## Phase 1 — Resolve branch name

**If `$ARGUMENTS` is a full branch name** (contains `/`), use it as given and jump to **→ Validate**.

**If `$ARGUMENTS` is exactly `--no-auto`**, run the interactive flow below (Steps 1–2).

**Otherwise** (`$ARGUMENTS` is empty), run **Auto mode** below — this is the default.

### Auto mode — infer type and description from context

Auto mode picks a representative branch name without asking the user anything. Do not show the type menu or the description prompt below in this mode.

1. **Determine intent**, in priority order:
   - The current conversation — the feature, fix, or task just discussed or requested.
   - If that's inconclusive, uncommitted work: run `git status --short` and `git diff` to see what's being changed.
   - If neither gives a clear signal, this is a genuine ambiguity — fall back to the interactive flow below (Steps 1–2) instead of guessing.

2. **Pick a type** from the same set used by the interactive menu: `feat`, `fix`, `hotfix`, `release`, `chore`.

3. **Build a description** using the same rules the interactive flow uses — read `~/.claude/skills/git-new-branch/references/conventional-branch-spec.md` and apply its translation patterns: lowercase kebab-case, 3–5 words, concise and purpose-driven, no leading/trailing/consecutive hyphens.

4. **State the decision in one line**, then continue immediately to **→ Validate** — do not pause for input:
   ```
   Auto: creating branch '<type>/<description>' — <one-clause reason>.
   ```

### Interactive flow (`--no-auto` only)

#### Step 1 — Type

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

#### Step 2 — Description

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
