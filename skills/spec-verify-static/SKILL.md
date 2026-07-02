---
name: spec-verify-static
description: >
  Statically verify that every numbered Behavior invariant in functional-spec.md has
  test coverage. Greps the implementation's test files for each invariant and produces
  a per-invariant covered/uncovered report. No app launch. Use after spec-implement,
  before spec-verify-dynamic.
disable-model-invocation: true
argument-hint: "<initiative-name>"
allowed-tools: Read Grep Glob Write Bash(git rev-parse:*)
when_to_use: >
  Invoke after spec-implement is complete, before spec-verify-dynamic. Use when the
  user wants to confirm each functional spec invariant is exercised by a test, without
  running the application.
effort: high
---

Statically verify every numbered Behavior invariant in `functional-spec.md` against the
implementation's tests. Searches test files for coverage of each invariant and prints a
per-invariant covered/uncovered report. This skill never launches the app — that is the
job of `spec-verify-dynamic`.

## Step 1 — Accept initiative name

`$ARGUMENTS` is the initiative name (e.g. `my-feature`). If empty, ask:

```
Which initiative should be statically verified? (kebab-case name):
```

## Step 2 — Resolve project root

Run `git rev-parse --show-toplevel`. Use the result as `<root>`. If it fails, use the
current working directory and note it.

## Step 3 — Check prerequisites

Print:
```
Checking prerequisites…
```

Read each in sequence. Stop at the first missing one:

- `<root>/initiatives/<name>/functional-spec.md` — if missing:
  ```
  initiatives/<name>/functional-spec.md not found. Run /spec-functional first.
  ```
- `<root>/initiatives/<name>/logbook.md` — if missing:
  ```
  initiatives/<name>/logbook.md not found. Run /spec-implement first.
  ```

## Step 4 — Clear previous report

If `<root>/initiatives/<name>/verify-static-report.md` exists, delete it before proceeding.

## Step 5 — Extract invariants

Read `functional-spec.md`. Collect all numbered list items under the `## Behavior`
heading (and any sub-headings within it).

If no numbered invariants are found, stop:
```
functional-spec.md has no numbered Behavior invariants to verify.
```

Print:
```
Found <N> invariants.
```

## Step 6 — Static phase

Print:
```
Static phase — checking test coverage for <N> invariants…
```

1. Read `logbook.md` to identify implementation files. Locate corresponding test
   files from those references. If `logbook.md` references no implementation files,
   use the full project test suite and note this in the report.
2. For each invariant, use Grep to search the test files for test cases that exercise
   the described behavior. After each one, print one line:
   ```
   <N>. ✓ <file>:<line> — <one-phrase summary>
   <N>. ✗ no coverage — <one-phrase explanation of why or what's missing>
   ```
3. Record: `covered — <file>:<line>` or `no coverage found`.

## Step 7 — Report

Write the report to `<root>/initiatives/<name>/verify-static-report.md`, overwriting any
previous run. Also print it to the conversation.

Format:

```
# Static verify report — <name>
Date: <YYYY-MM-DD>

Invariant N — <first line of invariant text>
  Static: covered — <file>:<line>  |  no coverage found

...

<N> invariants — <C> covered, <U> uncovered
```

After printing the report, output:

```
Next: /spec-verify-dynamic <name>
```

`spec-verify-static` produces no other side effects — safe to run multiple times.
