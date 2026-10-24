---
name: spec-implement
description: >
  Implements a full technical-spec.md spec end-to-end. Decomposes the implementation
  sequence into ordered phases, classifies each as scaffolding (build config,
  schema, project setup) or TDD (logic, handlers, components), then drives each
  phase to completion using the right agent strategy. Scaffolding phases use a
  setup agent; TDD phases run red-green-refactor cycles. Maintains a master log
  across all phases. Part of the spec-* family: run after spec-functional and
  spec-technical.
disable-model-invocation: true
argument-hint: "<initiative-name> | <path to technical-spec.md>"
allowed-tools: Read Glob Bash Agent
when_to_use: >
  When you want to implement a full technical-spec.md spec using TDD for logic phases
  and a setup agent for scaffolding phases. Run after spec-technical has produced
  a technical-spec.md. Invoke as /spec-implement <name> or
  /spec-implement <path-to-technical-spec.md>.
effort: high
hooks:
  PreToolUse:
    - matcher: "Write|Edit|Bash"
      hooks:
        - type: command
          command: "python3 ~/.claude/skills/spec-implement/scripts/guard.py"
---

# spec-implement

Orchestrates the full implementation of a `technical-spec.md` spec by decomposing it
into ordered phases and driving each to completion. Scaffolding phases (build
config, schema DDL, project setup) are handed to a setup agent. Logic phases
(pure functions, handlers, API endpoints, UI components) are driven by
red-green-refactor TDD cycles.

## Scripts

Bookkeeping is done by scripts, not by hand. Run each as
`python3 ~/.claude/skills/spec-implement/scripts/<name>.py <flags>` — one command per
Bash call, no chaining. Each prints `key=value` lines starting with `status=` (the
scanner prints JSON); `status=error` carries `message=` and `hint=` and exits 2. Run a
script with `--help` for its flags.

| Script | Does |
|---|---|
| `resolve-spec.py` | Step 1: argument to spec paths |
| `scan-project.py` | Step 2 and phase prerequisites: existing files, runners, layers with no test harness |
| `log.py` | Every `logbook.md` write: `init`, `resume`, `cycle`, `cycle-done`, `phase-done`, `close` |
| `stall.py` | Step 6f: continue / note / stop decision from the logged cycles |
| `guard.py` | Hook (frontmatter): blocks the orchestrator from writing anything but the logbook |

**If a script exits non-zero:** print its `message=` and `hint=`, and stop. Do not
re-implement what the script does by hand, and do not retry with different flags unless
the hint says to.

## HARD CONSTRAINTS

**You must never write source code, config files, or test files.** This applies
unconditionally — not even as a workaround:

- Do not call `Write`, `Edit`, or `Bash` to create or modify any implementation,
  test, build, or config file.
- Do not use heredocs, `cat >`, `tee`, or any shell command to write code. (The one
  allowed heredoc feeds text to `log.py` on stdin.)
- You never edit `logbook.md` directly either: `log.py` is the only writer.
- All code writing goes through the `Agent` tool. No exceptions.

The `guard.py` hook denies violations — treat a denial as a stop sign, not an obstacle.
Even when a change is one line or "just a config tweak", delegate it.

---

## Step 1 — Read the Spec

Run `resolve-spec.py --arg "$ARGUMENTS"`. It stops with the exact message when the
argument is empty or the spec is missing; relay that message and stop.

Read `technical=` with the `Read` tool. Also read `functional=` if non-empty — it
provides the behavioral invariants that TDD phases must satisfy.

---

## Step 2 — Scan the Project

Run `scan-project.py --spec <technical>`. From the JSON:

- `existing` / `missing`: which spec paths are already on disk (skip phases whose
  outputs all exist). It is a heuristic over backticked paths — confirm with `Read` or
  `Glob` when a phase looks half-done.
- `layers`: the test runner per layer (`runner`). A layer with `runner: null`, and any
  layer the spec implies but has no manifest yet, has no test framework: note
  > "No test framework detected for <layer>."

  Step 3 inserts a **[Scaffold]** test-harness phase immediately before the first TDD
  phase of that layer. The tdd-red agent must be able to assume a working test runner.

Then run `git status --short` on its own. If the working tree has uncommitted changes,
print and wait for a text reply:

```
The working tree has uncommitted changes — implementation edits will mix with them.
(a) Proceed
(b) Cancel
```

On (b): stop.

---

## Step 3 — Derive the Phase Plan

Before classifying, read `~/.claude/skills/spec-implement/references/classification.md`.

Parse the spec's **Implementation sequence** section — the ordered, numbered phase
list `spec-technical` writes — into an ordered list of phases. If the spec predates
that section and has none, fall back to deriving the order from the **Proposed changes**
section instead.

Classify each item by the nature of its output, never by the spec's testing policy:

- **[Scaffold]** — config, build system, DDL, project structure, wiring with no logic.
- **[TDD]** — functions, handlers, components with discrete testable behavior.
- Mixed item → split into [Scaffold] then [TDD]. Missing test harness → insert a
  [Scaffold] harness phase before the first [TDD] phase of that layer.
- Phase whose output files already exist → **[Done — skip]**.

---

## Step 4 — Confirm the Phase Plan

Present the full plan to the user. The example below uses a generic task-manager
REST API + SPA to illustrate the format — your actual phase names and numbers
will differ:

```
Phase plan derived from <spec>:

1. [Scaffold] dependency manifest — package manager manifest, lockfile
2. [Scaffold] directory layout — src/, src/handlers/, src/models/, frontend/src/
3. [Scaffold] database schema — CREATE TABLE tasks, users, tags; indexes
4. [Scaffold] backend test harness — zig build test step, src/tests/ directory
5. [TDD]      src/validation.py — validate_task, sanitize_fields     [Done — skip]
6. [TDD]      src/db.py — connection pool, query helpers, transactions
7. [TDD]      src/handlers/tasks.py — CRUD endpoints, pagination, filters
8. [TDD]      src/handlers/auth.py — token verification, role enforcement
9. [Scaffold] src/main.py — app bootstrap, route registration, middleware wiring
10. [Scaffold] frontend/ scaffold — bundler config, tsconfig, dev server
11. [Scaffold] frontend test harness — vitest config, test script in package.json
12. [TDD]      frontend/src/api.ts — typed fetch wrappers, error handling
13. [TDD]      frontend/src/pages/TaskListPage.tsx — fetch lifecycle, render
14. [TDD]      frontend/src/components/* — TaskRow, FilterBar, NewTaskForm
```

Then run `log.py status --log <dir>/logbook.md` (if it exits non-zero because the file
is missing, treat it as `kind=none`). `kind=session` is a resumable implementation log;
`kind=stub` (a `spec-initiative` log without `last-completed-phase`) and `kind=none`
mean no existing log — Step 5 merges into a stub rather than overwriting it.

**If `kind=session`**, read `last_completed=` as `<N>` and print — do not use
`AskUserQuestion`:

```
Found an existing session (initiatives/<name>/logbook.md).
Last completed phase: <N>.

(a) Resume from phase <N+1>
(b) Start from a specific phase — enter its number
(c) Start over — overwrite the existing log
(d) Cancel
```

Wait for a text reply. On (b): ask which phase number. On (c): proceed as if no log existed. On (d): stop.

**Otherwise**, print — do not use `AskUserQuestion`:

```
(a) Start from the first pending phase
(b) Start from a specific phase — enter its number
(c) Cancel
```

Wait for a text reply. On (b): ask which phase number and skip earlier phases. On (c): stop.

---

## Step 5 — Initialize or Resume the Log

The log lives at `initiatives/<name>/logbook.md`, co-located with the specs — one
shared `logbook.md` per initiative. `log.py` owns it.

**Starting fresh** (no log, a stub, or "start over"): run `log.py init` with
`--spec <technical>`, `--feature <feature-name>`, `--intro` (an opening paragraph: what
is being built, the full phase plan, the starting phase, and what "done" looks like),
and `--plan` (the numbered phase plan; pass `-` and a heredoc for multi-line text). Add
`--overwrite` only for "start over". It creates the file, merges into a stub (keeping the
stub's `started` and `status`), or overwrites a session log.

**Resuming** (resume, or start from a specific phase, against an existing session): run
`log.py resume --log <log> --from <N>`.

Tell the user the log path and the phase being started or resumed from.

**Load TDD lessons** (for use in all TDD phases): read
`~/.claude/tdd/lessons/LESSONS.md`. If it exists, read all linked lesson
files and collect their content as **lesson context**. If absent, lesson
context is empty.

---

## Step 6 — Execute Phases

For each pending phase in order, print:

```
━━━ Phase <N>/<total>: <name> [<Scaffold|TDD>] ━━━
```

Before the phase, run `scan-project.py --spec <technical> --require <path> ...` with
every file prior phases produced that this phase imports or depends on. If it prints
`"status": "missing"`, stop and report `required_missing` — a prior phase failed or was
skipped.

If `technical-spec.md` documents that this phase depends on an external service
(e.g. a docker-compose-based test harness, a local database container), **you**
— the orchestrator, never a scaffolding/TDD sub-agent — start it before invoking
any agent for this phase, and restart it if this phase adds new schema or
fixtures the service needs to pick up. Sub-agents' Bash access is scoped to
language-specific test/build commands only; they cannot manage infrastructure
themselves. Stop the service again at Step 7 (Close), unless told to leave it
running.

Then execute according to type.

---

### Scaffolding Phase

Before invoking the agent, verify the phase output contains no business logic.
If the files to be written include functions with validation rules, calculated
outputs, or conditional branching on domain inputs, this phase was misclassified
— stop, reclassify it as **[TDD]**, and execute it as a TDD phase instead.

Invoke the `Agent` tool with `subagent_type: "claude"`. That agent type has every tool,
so the prompt must restate its limits. The prompt must include:

1. The spec excerpt describing exactly what this phase produces (files, schema,
   config structure).
2. The list of files already on disk (so the agent avoids overwriting them).
3. The build verification command appropriate for the project's stack.
4. This instruction:
   > Create the scaffolding exactly as specified. Do not add logic beyond what
   > the spec defines for this phase. Write only the files listed for this phase.
   > Never edit `initiatives/*/logbook.md`, and do not start or stop services.
   > After writing all files, verify the project builds or installs cleanly (e.g.
   > `npm install`, `cargo build`, `go build ./...`, `pip install -e .`, or the
   > appropriate command). Report each file written and any errors.

Wait for the agent to complete. Capture: files written, verification result.

If the agent reports a build error: **stop**. Report the error and the list of
files written. Do not attempt to fix it automatically — ask the user to resolve
it and re-run from this phase.

Record the phase: `log.py phase-done --log <log> --phase <N> --type Scaffold --name <name> --summary <files written, verification result>`.

---

### TDD Phase

Run a focused TDD loop for this phase. The loop ends when the phase goal is
fully implemented.

#### 6a — Phase Context

Gather context to pass to every agent in this phase:

- The spec excerpt for this phase (its specific functions, endpoints, or
  components and their expected behavior).
- The functional-spec.md invariants that this phase covers (reference them by number).
- A list of all files produced by prior phases that this phase may import or
  depend on.
- The test runner command for this layer — `runner` for the layer in the
  `scan-project.py` output (e.g., `pytest tests/`, `go test ./...`, `cargo test`,
  `npm test`, `npx vitest run`, `bundle exec rspec`).

#### 6b — Derive the Next Behavior

Read all test and implementation files produced so far in this phase (and
any prerequisite files from prior phases). Determine **one** next minimal
behavior based on what the spec requires and what has not yet been tested.

The behavior must:
1. Name the exact function, method, or component under test
2. Specify exact inputs (concrete values or types)
3. State the exact expected output or side effect
4. Be a single unambiguous sentence

Print:
```
→ Cycle <N>.<K>: <behavior>
```

**Record the cycle before invoking any agent:**
`log.py cycle --log <log> --phase <N> --n <K> --behavior <behavior>`.

#### 6c — Red

Invoke `tdd-red` via the `Agent` tool. Pass:
- The phase context (spec excerpt, prerequisite files, test runner command)
- The exact behavior to test

`tdd-red` can write and edit files and run test commands only; it must write only the
test for this behavior and touch no implementation file.

Wait for completion. Capture: test file, test name.

If the agent fails: report the error and stop. Do not proceed to Green.

#### 6d — Green

Invoke `tdd-green` via the `Agent` tool. Pass:
- The test file and test name from Red
- The phase context (so the agent knows which modules to import)
- If lesson context is non-empty:
  > "Before writing implementation, review these TDD anti-patterns and avoid
  > them: [lesson context]"

`tdd-green` must never touch test files; it writes the minimum implementation and
verifies the tests are green.

Wait for completion. Capture: implementation files changed.

If the agent fails: report the error and stop.

#### 6e — Refactor

Invoke `tdd-refactor` via the `Agent` tool. Pass:
- The phase context
- All implementation files accumulated in this phase so far (every cycle)

`tdd-refactor` must introduce no new behavior, never touch test files, and verify the
tests stay green.

Wait for completion.

#### 6f — Log and Evaluate

Count the phase's covered behaviors: every function, endpoint, component, error path,
and invariant in the spec excerpt that now has a passing test. Record the cycle:
`log.py cycle-done --log <log> --phase <N> --n <K> --covered <count> --summary <red / green / refactor one-liner>`.

Print:
```
✓ Red: <test name>
✓ Green: <implementation files changed>
✓ Refactor: <what changed, or "nothing">
Cycle: <N>.<K>
```

Run `stall.py --log <log> --phase <N>` and act on `status=`:

- `continue` — keep cycling unless the phase is complete (below).
- `note` — print a one-line progress note (covered / remaining) and **keep going** — do not ask.
- `stop` — stop and ask the user (`reason=stalled`: 3 consecutive cycles added no new
  covered behavior; `reason=max-cycles`: 30 cycles). Report what was and was not
  implemented, and offer: continue, split the phase, or move on leaving it partial.

**Completeness is your judgment**, made against the spec excerpt, not a cycle count: list
every function, endpoint, component, error path, and covered invariant in the phase,
and keep cycling until each has a passing test. A phase with many behaviors legitimately
needs many cycles — even when the first few cycles went green, keep going.

**When complete**: print `✓ Phase <N> complete`, then run
`log.py phase-done --log <log> --phase <N> --type TDD --name <name> --summary <behaviors tested, files written, cycles taken, deviations from spec>`
and move to the next phase.

---

### Do not stop early

After Step 4's confirmation, run Steps 6–7 to completion without pausing. Do
not end your turn, summarize progress, or ask "shall I continue?" between
cycles or between phases. The only legal stops are those in **When to Stop and
Ask**, a `stop` from `stall.py`, a script or agent failure, and the dirty-tree
menu in Step 2. A phase is complete only when every behavior in its spec excerpt has
a passing test.

---

## Step 7 — Close

If you started any external service for a phase in Step 6, stop it now, unless
the user asked to leave it running.

When all phases are complete (or the user halts early), print a final summary:

```
Implementation complete.

Phases executed:    <S> scaffolding, <T> TDD
Total TDD cycles:   <count>
Files created:      <count>
Phases skipped:     <count>
```

Then run `log.py close --log <log> --summary <closing paragraph> --files -` with the
list of every file written or modified across all phases on stdin, one path per line.
The closing paragraph says what was built, how the design evolved from the spec, and
any deviations or surprises noted during implementation. `close` sets `status: complete`
and appends the `## Implementation files` section.

Finally, print:

```
Next: /spec-verify-static <name>, then write .claude/skills/run-<name>/SKILL.md and /spec-verify-dynamic <name>
```

---

## When to Stop and Ask

- A phase's prerequisite files do not exist (`scan-project.py --require` reports
  them): stop and report before attempting the phase.
- The spec's implementation sequence is ambiguous or missing: ask the user
  how to order the phases before deriving the plan.
- A scaffolding agent produces output that contradicts a spec constraint: stop
  and report — do not proceed to the next phase.
- A TDD phase needs to write a file that a later phase in the plan also owns:
  flag the overlap and ask whether to merge the phases or adjust boundaries.
- The user asks to pause: stop cleanly after the current cycle completes,
  report where things stand, and confirm how to resume.
