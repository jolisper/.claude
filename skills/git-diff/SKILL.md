---
name: git-diff
description: Summarize uncommitted changes and check semantic coherence — responsibility fit and consistency — before committing
disable-model-invocation: true
allowed-tools: Bash(git diff:*) Bash(git status:*) Read Grep
---

**Rule: run every command as a single, standalone call. Never use `&&`, `;`, pipes, or compound expressions. One command per tool call.**

## Step 1 — Collect changes

Run these three commands separately:
- `git diff --stat` — unstaged changes
- `git diff --cached --stat` — staged changes
- `git status --short` — untracked files

If there are no changes at all (no staged, no unstaged, no untracked), say "Nothing to diff — working tree is clean." and stop.

## Step 2 — Read context

For each changed file (staged or unstaged):
- Read the full file to understand its existing responsibilities, naming, and structure
- Note the class/module name, its apparent single responsibility, and existing method names
- This is your baseline for the semantic checks in Step 4

## Step 3 — Summarize changes

Run each command separately — never combine with `&&`, `;`, or pipes:
- `git diff`
- `git diff --cached`

Group changed files by logical concern (same feature, same fix, same refactor). For each group, write a plain-language summary:
- What was added, removed, or modified
- What the apparent intent is

## Step 4 — Semantic checks

### Responsibility fit

For each changed file, ask: does the change belong here?
- Does the added/modified code align with the class's existing responsibility?
- Does the class name still accurately describe what it does after the change?
- If a new method was added, does it fit the class's cohesion, or does it introduce a new concern?

Flag as: `[RESPONSIBILITY] <ClassName> — <what was added> may not belong here because <reason>`

### Consistency

Look for related places that should have changed but didn't:
- Use Grep to find other usages of renamed or modified symbols
- Check if similar patterns elsewhere follow the same change (e.g. a naming convention updated in one place but not others)
- Check if a concept was changed in implementation but not in tests, or vice versa

Flag as: `[CONSISTENCY] <symbol or concept> — changed in <location> but not in <related location>`

## Step 5 — Report

Produce the report in this format:

```
Summary of changes:

── Group 1: <description> ──
   • File1.java — <what changed>
   • File2.java — <what changed>

── Group 2: <description> ──
   • File3.java — <what changed>

Semantic findings:

[RESPONSIBILITY] PaymentService — added sendEmail() may not belong here (email is not a payment concern)
[CONSISTENCY] Movement.netAmount() — renamed in MovementGroupAggregate but original name still used in 2 test files

No issues found: <list any checks with no violations>
```

If no semantic issues are found, say so explicitly — a clean report is useful confirmation.
