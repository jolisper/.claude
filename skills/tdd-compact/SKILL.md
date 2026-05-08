---
name: tdd-compact
description: >
  Compact TDD lessons in ~/.claude/tdd/lessons/ into one lesson per category.
  Reads all lesson files, categorizes them using ~/.claude/tdd/lessons/CATEGORIES.md
  (created and maintained by this skill), synthesizes a single compacted lesson per
  category, archives originals to a timestamped backup directory, and rebuilds
  LESSONS.md. Run after accumulating several lesson files to keep the lesson set lean
  and actionable for TDD agents.
disable-model-invocation: true
effort: high
when_to_use: >
  After several TDD lesson files have accumulated in ~/.claude/tdd/lessons/ and you
  want to reduce them to one canonical lesson per category.
allowed-tools: Read Glob Bash(mkdir:*) Bash(mv:*) Bash(date:*) Write
---

# TDD Lesson Compactor

Reduce the TDD lesson set to one lesson per category. Synthesize all lessons in each
category into a single, pattern-rich document that TDD agents can follow without
ambiguity.

**Important**: Never use `&&`, `||`, `;`, or pipes in Bash calls — run each command
as a separate Bash call.

## Step 1 — Read all lessons

Glob `~/.claude/tdd/lessons/*.md` to list lesson files. Read every file found,
excluding `LESSONS.md` and `CATEGORIES.md`.

If no lesson files are found after excluding those two, report:
"No lesson files found in ~/.claude/tdd/lessons/ — nothing to compact." and stop.

## Step 2 — Load or derive categories

Read `~/.claude/tdd/lessons/CATEGORIES.md`.

- **File exists**: use its category list as the working set.
- **File does not exist**: derive an initial category set from the lesson content you
  read in Step 1. Use TDD-specific categories such as:
  `green-phase-over-generalization`, `trivially-passing-tests`, `red-phase-discipline`,
  `refactor-scope`, `test-design`. Avoid generic names like "bugs" or "mistakes".
  Write the initial CATEGORIES.md now (format below) and continue.

**CATEGORIES.md format:**
```
# TDD Lesson Categories

- **<slug>**: <one-sentence description of what lessons in this category cover>
- ...
```

## Step 3 — Categorize

Assign each lesson to the best-matching category from CATEGORIES.md. If a lesson
doesn't fit any existing category, add a new TDD-focused category to CATEGORIES.md
(Write the updated file) and assign the lesson to it.

Build the map: `{ category-slug → [lesson-filename, ...] }`.

## Step 4 — Present and confirm

Show the categorization:

```
Categorization:

<category-slug> (N lessons):
  • <file1.md>
  • <file2.md>

<category-slug> (1 lesson — carried over as-is):
  • <file.md>

...

How do you want to proceed?
(a) Continue
(b) Abort
```

Wait for explicit confirmation. On (b): stop.

## Step 5 — Synthesize

For each category with **2 or more lessons**:

1. Identify the shared core: what TDD principle do all lessons in this category
   violate? What is the common trigger and the correct minimum-implementation response?
2. Write a compacted lesson (format below) that captures all shared patterns in the
   Anti-pattern and Correct approach sections, then preserves each original lesson's
   concrete code example as a separate `## Variant` block.

For categories with **exactly 1 lesson**: carry it forward as-is, output to
`<category-slug>.md` (no synthesis needed).

**Lesson file format:**
```
---
name: <Title Case Name>
description: <one-sentence summary of the anti-pattern>
---

## Anti-pattern
<What the green phase does wrong — general description covering all variants.>

## Why it's a problem
<Why this breaks the red-green-refactor cycle.>

## Correct approach
<The minimum-implementation principle to follow.>

## Example
<Most representative concrete example with before/after code.>

## Variant
<Second original lesson's concrete example.>

## Variant
<Third original lesson's concrete example, if applicable.>
```

Output filename: `<category-slug>.md`

Store all synthesized content in memory — do not write to disk yet.

## Step 6 — Confirm before archiving

Show a summary of the planned changes:

```
Synthesis complete.

Compacted lessons:
  • <category-slug>.md (synthesized from N originals)
  • <category-slug>.md (carried over)
  ...

Originals to archive → ~/.claude/tdd/lessons-archive/<date>/
  • <original-file1.md>
  • <original-file2.md>
  ...

LESSONS.md will be rebuilt.

How do you want to proceed?
(a) Archive originals and write compacted lessons
(b) Abort
```

Wait for explicit confirmation. On (b): stop. No files have been written or moved yet.

## Step 7 — Archive originals

Run `date +%Y-%m-%d` to get today's date.
Run `mkdir -p ~/.claude/tdd/lessons-archive/<date>`.

For each original lesson file, run one `mv` call per file:
`mv ~/.claude/tdd/lessons/<filename> ~/.claude/tdd/lessons-archive/<date>/<filename>`

If any `mv` fails: report which file failed and stop. Do not proceed to Step 8.
The partially archived files remain in the backup directory — nothing is lost.

## Step 8 — Write compacted lessons

Write each compacted (or carried-over) lesson to:
`~/.claude/tdd/lessons/<category-slug>.md`

If any Write fails: report which file failed and stop. The originals are safe in the
archive directory.

## Step 9 — Rebuild LESSONS.md

Write a new `~/.claude/tdd/lessons/LESSONS.md`:

```
# TDD Lessons

- [<name>](<category-slug>.md) — <description>
- ...
```

## Step 10 — Summary

```
Done.

  <N> lessons → <M> lesson files
  Archive: ~/.claude/tdd/lessons-archive/<date>/
```

## When NOT to run this skill

Stop and warn the user if:
- `~/.claude/tdd/lessons/` does not exist.
- Every category already has exactly one lesson — the set is already compact.
