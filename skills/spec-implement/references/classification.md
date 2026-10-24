# Phase classification

Classify each item of the spec's implementation sequence by the nature of its output.

## Scaffolding phase

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

## TDD phase

Output contains functions, handlers, or components with discrete, testable
behaviors. Mark as **[TDD]**. Examples:
- Pure utility or domain modules (`validation.py`, `money.go`, `date_utils.ts`)
- DB query helpers and repository functions (beyond raw schema)
- REST or RPC handlers (`handlers/tasks.go`, `routes/users.py`, `api/orders.ts`)
- Service or use-case classes (`OrderService`, `AuthService`)
- Frontend API clients and typed fetch wrappers (`api.ts`, `client.py`)
- UI components and pages (`TaskListPage.tsx`, `UserRow.vue`, `LoginForm.svelte`)

## Split when mixed

If a spec item contains both scaffolding and logic (e.g., a `db.py` that holds
both `CREATE TABLE` DDL and query helper functions), split it into two
consecutive sub-phases: **[Scaffold]** first, **[TDD]** second.

## Insert test harness phases when needed

Before the first **[TDD]** phase for each language/layer (backend, frontend,
etc.), check whether a working test framework already exists for that layer
(`no_harness` in the `scan-project.py` output). If not, insert a **[Scaffold]**
phase immediately before it:

    [Scaffold]  test harness — install test framework, write config,
               create tests/ directory, verify <test command> exits 0 on empty suite

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

## Classification pitfalls — do not do this

**The spec's testing strategy does NOT affect classification.**
A spec that says "manual testing only" or "add unit tests in Phase 2" is
expressing a project policy about test maintenance — it does not make logic
phases into scaffolding phases. Classify by the nature of the output, always:

- Validation rules, SQL queries, arithmetic, conditional branching → **[TDD]**
- Routing tables, config files, DDL, server startup wiring → **[Scaffold]**

If you find yourself classifying a handler, component, or domain function as
**[Scaffold]** because the spec doesn't mention unit tests for it, stop and
reclassify it as **[TDD]**. The absence of tests is exactly why TDD is needed.
