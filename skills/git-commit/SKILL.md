---
name: git-commit
description: >
  Use this skill when the user wants to stage and commit changes. Invoke for
  requests like "commit my changes", "make a commit", or "stage and commit".
  Analyzes unstaged changes, groups them into logical commits, proposes a
  Conventional Commits message, and confirms before committing.
disable-model-invocation: false
allowed-tools: Bash(git:*) Bash(python3:*) Read
---

Stage changes and commit them using a Conventional Commits message. Follow this protocol:

**Important**: Never use `cd`, `git -C`, `&&`, or `||`. Run each command separately with no path arguments — rely on the shell's current working directory.

## Step 1 — Pre-flight check

Run each of these commands separately:

1. `git status`
2. `git diff --cached --stat`

## Step 2 — Stage check

If changes are already staged, skip to Step 3.

If nothing is staged (`git diff --cached --stat` shows no output):

1. **Analyze unstaged changes** — run `git diff --stat` and `git status --short` to get the full list of modified, added, and deleted files. Then read the diffs (`git diff`) to understand what each file's changes are about.

2. **Suggest staging groups** — analyze the changes and group files by logical purpose. Each group should represent a single coherent reason for a commit. Consider:
   - Files that share the same feature, fix, or refactoring goal belong together.
   - Test files should group with the production code they test.
   - Config/build file changes should group separately unless they're directly required by a feature change.
   - Unrelated changes (e.g. a typo fix alongside a new feature) should be separate groups.
   - **Intra-file splits**: a single file may contain hunks for different purposes (e.g. a bug fix and a formatting change, or a feature addition and an unrelated refactor). When the diff for a file has clearly separable hunks serving different goals, assign those hunks to different groups and mark the file as needing a partial stage. In the group presentation, annotate it: `<file> (partial — only <description> hunks)`.

3. **Present the analysis** — show the changes organized inside their suggested groups, so the user can see at a glance which changes go together and why. This is mandatory even when all files end up in a single group.

   Present each group as a suggested commit, with its files and their changes listed **inside** the group. For files that need splitting across groups, annotate which hunks belong to this group. After all groups, explain the grouping rationale in one sentence:

   ```
   Suggested commits:

   ── Commit 1: <type>(scope): <description> ──
      • <file1> — <what changed in this file>
      • <file2> — <what changed in this file>

      Reason: <why these changes belong together>

   ── Commit 2: <type>(scope): <description> ──
      • <file3> — <what changed in this file>
      • <file1> (partial — lines X–Y only) — <what this hunk does>

      Reason: <why these changes belong together>

   (a) Start with commit 1
   (b) Start with commit 2
   ...
   (<next>) Stage everything as a single commit
   (<next>) Stage specific files manually
   (<next>) Abort
   ```
   Letters are always sequential: one per group, then the fixed options continue from the next letter. For example, with 2 groups: (a) commit 1, (b) commit 2, (c) stage all, (d) manual, (e) abort. With 1 group: (a) stage and commit, (b) manual, (c) abort.

   If there is only one group, still use the same format (single commit block with its files and reason) — this makes it clear the agent considered splitting and decided everything belongs together.

   **Inseparable mixed concerns**: when the analysis identifies multiple distinct reasons for change (e.g. a format change and a refactor) but the changes affect the same lines of code and cannot be split into separate commits, explain this directly in the `Reason:` line:
   ```
   Reason: <N> distinct concerns (<concern 1> + <concern 2>), but they
           touch the same lines and can't be split into separate commits.
   ```
   This tells the user the agent considered splitting and explains why it didn't — rather than silently merging unrelated concerns.

4. **Execute the user's choice** — stage the selected files:
   - For whole files: `git add <files>`.
   - For partial files (intra-file splits): run `python3 ~/.claude/skills/git-commit/scripts/stage-hunks.py --help` to confirm the interface, then invoke it with `--file <path> --hunks <N,N,...>` (hunk numbers are 1-based, matching the order they appear in `git diff <file>`). Show the user which hunks are being staged and confirm before running.
   - After committing (Steps 3–7), if there are remaining groups, ask: "Ready to commit the next group?" and loop back to present the remaining groups.

## Step 3 — Analyze staged diff

Run `git diff --cached` and read the full output to understand what is being committed.

## Step 4 — Sensitive data scan

Using the diff output from Step 3, scan only the staged changes (added lines and new file contents) for sensitive data. Do **not** scan the rest of the project — only what appears in the diff.

Read `references/sensitive-patterns.md` for the full list of credential patterns and sensitive file types to check. Then scan the diff in two passes:

1. **Changed lines** — inspect every `+` line for hardcoded secrets and credentials.
2. **Staged filenames** — check the `diff --git a/... b/...` header lines for sensitive file types.

**If any sensitive data is found**, show the warning block defined in the "Warning block format" section of `references/sensitive-patterns.md` before proceeding. Do **not** proceed to Step 5 until every flagged item is resolved or the user explicitly confirms in writing that the data is intentional and safe ("I confirm this is not sensitive / proceed anyway").

**If nothing is found**, continue silently to Step 5.

## Step 5 — Propose a commit message

Based on the diff, suggest a Conventional Commits message:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Multiple concerns in one commit**: if the staged changes contain inseparable mixed concerns (identified in Step 2), the commit message must reflect all of them — not just the dominant one. Use the subject line for the primary concern, and list the other concerns as bullet points in the body. For example:
```
fix(esco3): align match log format with structured pattern

- refactor: merge split anyMatch assertions into single combined condition
```

Show the proposed message clearly, then ask the user to:
- (a) confirm and use it as-is
- (b) edit it (ask for their edits)
- (c) provide their own message entirely

## Step 6 — Commit

Run `git commit -m "<message>"`. If the message has a body, use multiple `-m` flags (one per paragraph) or a single `-m` with embedded newlines.

## Step 7 — Summary

Show the commit hash and one-line summary from the output of `git log -1 --oneline`.
