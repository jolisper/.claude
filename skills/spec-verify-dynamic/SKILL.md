---
name: spec-verify-dynamic
description: >
  Dynamically verify that every numbered Behavior invariant in functional-spec.md holds
  in the running application. Launches the app via a run recipe, exercises each invariant,
  and produces a per-invariant pass/fail report. Use after spec-verify-static, before
  spec-archive.
disable-model-invocation: true
argument-hint: "<initiative-name>"
allowed-tools: Read Grep Glob Write Bash(git rev-parse:*)
when_to_use: >
  Invoke after spec-verify-static, before spec-archive. Use when the user wants to
  confirm the running application actually behaves as each functional spec invariant
  describes.
effort: high
---

Dynamically verify every numbered Behavior invariant in `functional-spec.md` against the
running application. Launches the app via a run recipe, exercises each invariant, and
prints a per-invariant pass/fail report. This skill does not inspect test coverage — that
is the job of `spec-verify-static`.

**Hard rule — no test suites.** This skill verifies behavior against a *live process*. It
must NEVER run a unit, integration, or any other test suite (`mvn test`, `gradle test`,
`pytest`, `go test`, `npm test`, `bun test`, etc.). Running a test is not dynamic
verification — it is exactly what `spec-verify-static` already covered. Every observation
in this skill must come from exercising the started application: calling an HTTP/RPC
endpoint, invoking a CLI command, sending a message, or driving the UI. If an invariant
can only be reached through internal code that has no external surface, record it as
`skip — no runtime surface to exercise`; do not substitute a test run.

## Step 1 — Accept initiative name

`$ARGUMENTS` is the initiative name (e.g. `my-feature`). If empty, ask:

```
Which initiative should be dynamically verified? (kebab-case name):
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
- A run recipe — use Glob to find `<root>/.claude/skills/run-*/SKILL.md`. Take the
  first match as `<run-recipe>`. If none found:
  ```
  No run recipe found under .claude/skills/run-*/

  Run /run-skill-generator to create one. It will launch the app from a clean
  environment, capture what worked, and write the recipe automatically.

  Once the recipe exists, re-run /spec-verify-dynamic <name>.
  ```
  Do not create the recipe — that is the user's responsibility.

## Step 4 — Clear previous report

If `<root>/initiatives/<name>/verify-dynamic-report.md` exists, delete it before proceeding.

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

## Step 6 — Dynamic phase

Print:
```
Dynamic phase — launching app…
```

Read `<run-recipe>` (resolved in Step 3) and follow its instructions to launch
the app. Do not modify it.

> The dynamic phase may require tool permissions beyond this skill's `allowed-tools`
> depending on what the run recipe does. If prompted, approve commands from the recipe.

**Ensure a clean instance — restart if already running.** Feature flags and config are
usually read at boot, so an instance that is already up will not pick up the flags this
skill enables below. Using the run recipe's health check / port, determine whether the
app is already running. If it is, stop it and relaunch from scratch so a known baseline
and the correct flags apply. Prefer the recipe's own stop/teardown step; only if the
recipe defines none, fall back to stopping the process bound to its port. Print:
```
App already running — restarting for a clean instance…
```
Do not kill processes unrelated to this app's recipe.

If the app fails to start: record `skip — app did not start` for all invariants, report
the launch error, and proceed to Step 7.

**Enable feature flags.** The initiative's behavior is often gated behind one or more
feature flags that default to off. Before exercising anything, read `functional-spec.md`,
`logbook.md`, and the run recipe to identify every flag, toggle, or config switch that
gates the feature under verification, and turn them ON — via env var, config file,
admin/runtime toggle endpoint, or whatever mechanism the app exposes. A gated feature is
NOT "no runtime surface"; it is a flag you must activate. Print the flags you enabled:
```
Enabled feature flags: <flag> = <value>, …
```
Only if the feature genuinely cannot be enabled by any available mechanism, record those
invariants as `skip — feature flag could not be enabled` and report what you tried.

**Show the dependency map.** Before exercising any invariant, inspect the resolved
runtime configuration of the started app (env vars, config files, connection strings,
service URLs the recipe set) and list every external dependency it is wired to —
databases, caches, message brokers, external APIs, and any other backing service.
Classify each by where it points:

- **local** — runs on this machine or in-process (localhost, an embedded/testcontainer
  instance, a file-backed stub).
- **development** — a shared dev/staging/test environment.
- **production** — a live production endpoint.

Print the map and require explicit confirmation of the whole environment before
continuing — always, regardless of how the dependencies are classified:
```
Dependency map for this run:
  <dependency> → <target> [local | development | production]
  …

Confirm this environment before the test round begins. Proceed? (yes/no)
```
Do not begin the test round until the user confirms. If any dependency resolves to
**production** — or you cannot determine where it points, in which case label it
`unknown` and treat it as production — add a prominent warning above the prompt naming
those dependencies.

Print:
```
App running — exercising <N> invariants…
```

For each invariant in order:

1. Before exercising, print:
   ```
   <N>/<total> Testing: <first line of invariant text>…
   ```
2. Exercise the **running app** to observe whether the described behavior holds — send a
   real request to its endpoint, invoke the real function/command, or drive its UI, and
   read the actual response, logs, or side effects the live process produces. Do not run
   any test suite to stand in for this; an observation that comes from `mvn test` (or any
   `*test*` command) is invalid for this skill.
3. Immediately after, print the result on the next line:
   ```
   <N>. ✓ pass — <one-phrase summary of observed behavior>
   <N>. ✗ fail — <one-phrase observed vs expected>
   ```
4. Record `pass` or `fail — <observed vs expected>`. If the invariant has no externally
   reachable surface on the running app, record `skip — no runtime surface to exercise`
   instead of falling back to a test run.

## Step 7 — Report

Write the report to `<root>/initiatives/<name>/verify-dynamic-report.md`, overwriting any
previous run. Also print it to the conversation.

Format:

```
# Dynamic verify report — <name>
Date: <YYYY-MM-DD>

Invariant N — <first line of invariant text>
  Dynamic: pass  |  fail — <reason>  |  skip — app did not start  |  skip — feature flag could not be enabled  |  skip — no runtime surface to exercise

...

<N> invariants — <P> passed, <F> failed, <S> skipped
```

After printing the report, output:

```
Next: /spec-archive <name>
```

`spec-verify-dynamic` produces no other side effects — safe to run multiple times.
