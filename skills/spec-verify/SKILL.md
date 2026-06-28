---
name: spec-verify
description: >
  Verify that every numbered Behavior invariant in functional-spec.md is satisfied by
  the implementation. Runs static (test coverage) then dynamic (running app) phases
  and produces a per-invariant pass/fail report. Use after spec-implement, before
  spec-archive.
disable-model-invocation: true
argument-hint: "<initiative-name>"
allowed-tools: Read Grep Glob Write Bash(git rev-parse:*)
when_to_use: >
  Invoke after spec-implement is complete and before running spec-archive. Use when
  the user wants to confirm the implementation satisfies all functional spec invariants.
effort: high
---

Verify every numbered Behavior invariant in `functional-spec.md` against the implementation.
Runs two phases — static (test coverage) then dynamic (app exercise) — and prints a
per-invariant pass/fail report.

## Step 1 — Accept initiative name

`$ARGUMENTS` is the initiative name (e.g. `my-feature`). If empty, ask:

```
Which initiative should be verified? (kebab-case name):
```

## Step 2 — Resolve project root

Run `git rev-parse --show-toplevel`. Use the result as `<root>`. If it fails, use the
current working directory and note it.

## Step 3 — Check prerequisites

Read each in sequence. Stop at the first missing one:

- `<root>/initiatives/<name>/functional-spec.md` — if missing:
  ```
  initiatives/<name>/functional-spec.md not found. Run /spec-functional first.
  ```
- `<root>/initiatives/<name>/logbook.md` — if missing:
  ```
  initiatives/<name>/logbook.md not found. Run /spec-implement first.
  ```
- `<root>/.claude/skills/run-<name>/` directory — if missing:
  ```
  .claude/skills/run-<name>/ not found.
  Create a run recipe there with test environment variables and a non-production
  database configured, then re-run /spec-verify.
  ```
  Do not create the recipe — that is the user's responsibility.

## Step 4 — Extract invariants

Read `functional-spec.md`. Collect all numbered list items under the `## Behavior`
heading (and any sub-headings within it).

If no numbered invariants are found, stop:
```
functional-spec.md has no numbered Behavior invariants to verify.
```

## Step 5 — Static phase

1. Read `logbook.md` to identify implementation files. Locate corresponding test
   files from those references. If `logbook.md` references no implementation files,
   use the full project test suite and note this in the report.
2. For each invariant, use Grep to search the test files for test cases that exercise
   the described behavior.
3. Record: `covered — <file>:<line>` or `no coverage found`.

## Step 6 — Dynamic phase

Read `<root>/.claude/skills/run-<name>/skill.md` and follow its instructions to launch
the app. The run recipe defines the test environment — do not modify it.

> The dynamic phase may require tool permissions beyond this skill's `allowed-tools`
> depending on what the run recipe does. If prompted, approve commands from the recipe.

If the app fails to start: record `skip — app did not start` for all invariants, report
the launch error, and proceed to Step 7.

For each invariant in order:

1. Exercise the running app to observe whether the described behavior holds.
2. Record `pass` or `fail — <observed vs expected>`. If static covered but dynamic fails,
   record: `fail — tests pass but observed behavior does not match invariant`.

Do not skip a dynamic check because the static phase found no coverage for it — even
when static shows no tests, still exercise the invariant dynamically.

## Step 7 — Report

Write the report to `<root>/initiatives/<name>/verify-report.md`, overwriting any
previous run. Also print it to the conversation.

Format:

```
# Verify report — <name>
Date: <YYYY-MM-DD>

Invariant N — <first line of invariant text>
  Static:  covered — <file>:<line>  |  no coverage found
  Dynamic: pass  |  fail — <reason>  |  skip — app did not start

...

<N> invariants — <P> passed, <F> failed, <S> skipped, <U> uncovered
```

"Uncovered" = static found no test AND dynamic recorded `skip — app did not start`.

`spec-verify` produces no other side effects — safe to run multiple times.
