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
  when_to_use: >
    When you want to implement a full technical-spec.md spec using TDD for logic phases
    and a setup agent for scaffolding phases. Run after spec-technical has produced
    a technical-spec.md. Invoke as /spec-implement <path-to-technical-spec.md>.
  argument-hint: "<path to technical-spec.md>"
  effort: high
  ---

  # spec-implement

  Orchestrates the full implementation of a `technical-spec.md` spec by decomposing it
  into ordered phases and driving each to completion. Scaffolding phases (build
  config, schema DDL, project setup) are handed to a setup agent. Logic phases
  (pure functions, handlers, API endpoints, UI components) are driven by
  red-green-refactor TDD cycles.

  ## HARD CONSTRAINTS

  **You must never write source code, config files, or test files.** This applies
  unconditionally — not even as a workaround:

  - Do not call `Write`, `Edit`, or `Bash` to create or modify any implementation,
    test, build, or config file.
  - Do not use heredocs, `cat >`, `tee`, or any shell command to write code.
  - The only files you may write are the master log (`initiatives/<name>/implement-log.md`)
    and phase log entries within it.
  - All code writing goes through the `Agent` tool. No exceptions.

  Violations break the session. There are no exceptions.

  ---

  ## Step 1 — Read the Spec

  Resolve `$ARGUMENTS`:

  - If empty or whitespace-only, stop:
    > `spec-implement` requires a technical-spec.md path. Invoke as `/spec-implement initiatives/<name>/technical-spec.md`.
  - Read the file with the `Read` tool. If it does not exist, stop and tell the user.

  Also read the companion `functional-spec.md` in the same directory if it exists —
  it provides the behavioral invariants that TDD phases must satisfy.

  ---

  ## Step 2 — Scan the Project

  Use `Glob` and `Bash` to detect:

  - Which files from the spec's directory layout already exist (skip their phases).
  - The language(s) and test runner(s) in use or implied by the spec.
  - Any build manifests (`package.json`, `Cargo.toml`, `pyproject.toml`,
    `build.gradle`, etc.) or other build artifacts already present.

  Record what exists. Step 3 uses this to mark phases already done.

  If no test runner is found for a given language or layer, note it explicitly:
  > "No test framework detected for <layer>."

  Step 3 will insert a **[Scaffold]** phase to set up the test harness immediately
  before the first TDD phase for that layer. The tdd-red agent must be able to
  assume a working test runner exists when it runs.

  ---

  ## Step 3 — Derive the Phase Plan

  Parse the spec's **Implementation sequence** section (or equivalent) into an
  ordered list of phases.

  For each item in the sequence, classify it:

  ### Scaffolding phase
  Output is config, build system, DDL, or project structure with no testable
  behavioral logic. Mark as **[Scaffold]**. Examples:
  - Build manifests and lockfiles (`package.json`, `Cargo.toml`, `pyproject.toml`,
    `build.gradle`, `go.mod`)
  - Compiler or bundler config (`tsconfig.json`, `vite.config.ts`,
    `webpack.config.js`, `jest.config.ts`)
  - Directory layout creation (`src/`, `src/handlers/`, `tests/`, `frontend/src/`)
  - Database schema DDL (`CREATE TABLE` statements, indexes, migrations)
  - App entry point wiring with no business logic (routing table, server startup,
    middleware registration, DI container setup)

  ### TDD phase
  Output contains functions, handlers, or components with discrete, testable
  behaviors. Mark as **[TDD]**. Examples:
  - Pure utility or domain modules (`validation.py`, `money.go`, `date_utils.ts`)
  - DB query helpers and repository functions (beyond raw schema)
  - REST or RPC handlers (`handlers/tasks.go`, `routes/users.py`, `api/orders.ts`)
  - Service or use-case classes (`OrderService`, `AuthService`)
  - Frontend API clients and typed fetch wrappers (`api.ts`, `client.py`)
  - UI components and pages (`TaskListPage.tsx`, `UserRow.vue`, `LoginForm.svelte`)

  ### Split when mixed
  If a spec item contains both scaffolding and logic (e.g., a `db.py` that holds
  both `CREATE TABLE` DDL and query helper functions), split it into two
  consecutive sub-phases: **[Scaffold]** first, **[TDD]** second.

  ### Insert test harness phases when needed

  Before the first **[TDD]** phase for each language/layer (backend, frontend,
  etc.), check whether a working test framework already exists for that layer
  (detected in Step 2). If not, insert a **[Scaffold]** phase immediately before it:

  [Scaffold]  test harness — install test framework, write config,
             create tests/ directory, verify  exits 0 on empty suite

  Examples:
  - Zig backend, no test step → `[Scaffold]` Zig test harness: add `test` step to
    `build.zig`, create `src/tests/` directory, verify `zig build test` exits 0
  - React frontend, no Vitest → `[Scaffold]` Vitest setup: install vitest,
    write `vitest.config.ts`, add `"test"` script to `package.json`, verify
    `npx vitest run` exits 0 on empty suite
  - Python, no pytest → `[Scaffold]` pytest setup: add `[tool.pytest.ini_options]`
    to `pyproject.toml`, create `tests/__init__.py`, verify `pytest` exits 0

  The goal: when the first tdd-red cycle runs, the test runner command already
  works and exits 0 on an empty or passing suite.

  ### Classification pitfalls — do not do this

  **The spec's testing strategy does NOT affect classification.**
  A spec that says "manual testing only" or "add unit tests in Phase 2" is
  expressing a project policy about test maintenance — it does not make logic
  phases into scaffolding phases. Classify by the nature of the output, always:

  - Validation rules, SQL queries, arithmetic, conditional branching → **[TDD]**
  - Routing tables, config files, DDL, server startup wiring → **[Scaffold]**

  If you find yourself classifying a handler, component, or domain function as
  **[Scaffold]** because the spec doesn't mention unit tests for it, stop and
  reclassify it as **[TDD]**. The absence of tests is exactly why TDD is needed.

  ### Mark already-done phases
  Any phase whose output files already exist on disk (detected in Step 2) is
  marked **[Done — skip]**.

  ---

  ## Step 4 — Confirm the Phase Plan

  Present the full plan to the user. The example below uses a generic task-manager
  REST API + SPA to illustrate the format — your actual phase names and numbers
  will differ:

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

  Then check whether `initiatives/<name>/implement-log.md` exists and read its
  frontmatter.

  **If an existing log is found**, read `last-completed-phase` and present:

  ```
  Found an existing session (initiatives/<name>/implement-log.md).
  Last completed phase: <N>.

  (a) Resume from phase <N+1>
  (b) Start from a specific phase — enter its number
  (c) Start over — overwrite the existing log
  (d) Cancel
  ```

  On (b): ask which phase number.
  On (c): proceed as if no log existed.
  On (d): stop.

  **If no existing log is found**, present:

  ```
  (a) Start from the first pending phase
  (b) Start from a specific phase — enter its number
  (c) Cancel
  ```

  On (b): ask which phase number and skip earlier phases.
  On (c): stop.

  ---

  ## Step 5 — Initialize or Resume the Log

  The log lives at `initiatives/<name>/implement-log.md`, co-located with the
  specs. `<name>` is the initiative directory — the parent directory of the
  `technical-spec.md`.

  **If starting fresh** (no existing log, or user chose "start over" in Step 4):

  Write `initiatives/<name>/implement-log.md` with this structure:

  ~~~markdown
  ---
  spec: initiatives/<name>/technical-spec.md
  started: <YYYY-MM-DD>
  last-completed-phase: 0
  status: in-progress
  ---

  # Implementation Log: <feature-name>

  <opening paragraph: what is being built, the full phase plan, the starting
  phase, and what "done" looks like for this implementation>

  ## Phase Plan

  1. [Scaffold] ...
  ...
  N. [TDD] ...
  ~~~

  **If resuming** (user chose "resume" or "start from a specific phase" against
  an existing log):

  Read the existing log. Set the resume point from `last-completed-phase` or
  the user-specified phase number. Append a divider to the log:

  ~~~markdown

  ---
  Resumed: <YYYY-MM-DD>, starting from phase <N>
  ---
  ~~~

  Tell the user the log path and the phase being resumed from.

  **Load TDD lessons** (for use in all TDD phases): read
  `~/.claude/tdd/lessons/LESSONS.md`. If it exists, read all linked lesson
  files and collect their content as **lesson context**. If absent, lesson
  context is empty.

  ---

  ## Step 6 — Execute Phases

  For each pending phase in order:

  Print:
  ━━━ Phase /:  [] ━━━

  Then execute according to type.

  ---

  ### Scaffolding Phase

  Before invoking the agent, verify the phase output contains no business logic.
  If the files to be written include functions with validation rules, calculated
  outputs, or conditional branching on domain inputs, this phase was misclassified
  — stop, reclassify it as **[TDD]**, and execute it as a TDD phase instead.

  Invoke the `Agent` tool with `subagent_type: "claude"`. The prompt must include:

  1. The spec excerpt describing exactly what this phase produces (files, schema,
     config structure).
  2. The list of files already on disk (so the agent avoids overwriting them).
  3. The build verification command appropriate for the project's stack.
  4. This instruction:
     > Create the scaffolding exactly as specified. Do not add logic beyond what
     > the spec defines for this phase. After writing all files, verify the project
     > builds or installs cleanly (e.g. `npm install`, `cargo build`, `go build ./...`,
     > `pip install -e .`, or the appropriate command). Report each file written
     > and any errors.

  Wait for the agent to complete. Capture: files written, verification result.

  If the agent reports a build error: **stop**. Report the error and the list of
  files written. Do not attempt to fix it automatically — ask the user to resolve
  it and re-run from this phase.

  Update the master log with the phase result before moving to the next phase.

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
  - The test runner command for this layer (e.g., `pytest tests/`, `go test ./...`,
    `cargo test`, `npm test`, `npx vitest run`, `bundle exec rspec`).

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
  → Cycle .:

  **Update the master log before invoking any agent.**

  #### 6c — Red

  Invoke `tdd-red` via the `Agent` tool. Pass:
  - The phase context (spec excerpt, prerequisite files, test runner command)
  - The exact behavior to test

  Wait for completion. Capture: test file, test name.

  If the agent fails: report the error and stop. Do not proceed to Green.

  #### 6d — Green

  Invoke `tdd-green` via the `Agent` tool. Pass:
  - The test file and test name from Red
  - The phase context (so the agent knows which modules to import)
  - If lesson context is non-empty:
    > "Before writing implementation, review these TDD anti-patterns and avoid
    > them: [lesson context]"

  Wait for completion. Capture: implementation files changed.

  If the agent fails: report the error and stop.

  #### 6e — Refactor

  Invoke `tdd-refactor` via the `Agent` tool. Pass:
  - The phase context
  - All implementation files accumulated in this phase so far (every cycle)

  Wait for completion.

  #### 6f — Log and Evaluate

  Update the master log. Print:
  ✓ Red:
  ✓ Green:
  ✓ Refactor: <what changed, or "nothing">
  Cycle: .

  Assess whether this phase's goal is fully implemented:

  - **After 5 cycles without completion**: print a check-in and ask the user
    whether the scope is as expected or whether to adjust the phase boundary.
  - **After 7 cycles without completion**: stop. Report what was and was not
    implemented. Ask the user to either continue (extend the budget), split the
    phase, or proceed to the next phase leaving this one partial.
  - **When complete**: print `✓ Phase <N> complete`, then:
    1. Update `last-completed-phase: <N>` in the log frontmatter.
    2. Append a phase section to the log:
       ~~~markdown
       ## Phase <N> — [type] <name>
       <phase summary: behaviors tested, files written, cycles taken, deviations from spec>
       ~~~
    3. Move to the next phase.

  ---

  ## Step 7 — Close

  When all phases are complete (or the user halts early), print a final summary:

  Implementation complete.

  Phases executed:    scaffolding,  TDD
  Total TDD cycles:
  Files created:
  Phases skipped:

  Write the master log closing paragraph: what was built, how the design evolved
  from the spec, any deviations or surprises noted during implementation.
  Then update `status: complete` in the log frontmatter.

  ---

  ## When to Stop and Ask

  - A phase's prerequisite files do not exist (a prior phase failed or was
    skipped): stop and report before attempting the phase.
  - The spec's implementation sequence is ambiguous or missing: ask the user
    how to order the phases before deriving the plan.
  - A scaffolding agent produces output that contradicts a spec constraint: stop
    and report — do not proceed to the next phase.
  - A TDD phase needs to write a file that a later phase in the plan also owns:
    flag the overlap and ask whether to merge the phases or adjust boundaries.
  - The user asks to pause: stop cleanly after the current cycle completes,
    report where things stand, and confirm how to resume.