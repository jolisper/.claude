# Auto verification

Loaded by SKILL.md Step 8 only when `auto=true`, after `log.py close` ran. Carries the
implementation through static and dynamic verification and decides, without prompting,
whether findings justify new tests or corrections. A round is one verify → act cycle;
`rounds=` (2) comes from Step 1's `resolve-spec.py` output.

All commands are `python3 ~/.claude/skills/spec-implement/scripts/<name>.py <flags>`, one
per Bash call, no chaining. A state machine in `auto.py` owns the control flow: you never
decide what comes next, you ask.

## Ground rules

- You write no source, test, config, or spec file (42). All changes go through agents.
  `logbook.md` is written only by scripts: `log.py auto-start`, then `auto.py advance`.
- Never edit `functional-spec.md` or `technical-spec.md`, including for spec mismatches (31).
- Actions are limited to the findings: no features, no refactors, no files a finding does
  not implicate (30).
- The tdd agents only run commands starting with their test runner. You run the baseline
  and regression runs yourself, via Bash, with each layer's `runner` from `scan-project.py`.
- Auto mode adds no prompts of its own (4). Never answer a question an agent asks: report
  it as `{"error": "<question>"}`.
- **Delegated-step failure** (agent error, runner broken, script error, agent question):
  advance with `{"error": "<what>"}`. The machine ends the run at SUMMARY (37). Do not retry.

## Driver loop

1. `log.py auto-start --log <log> --rounds <rounds>` once. It appends the
   `## Auto verification` section and a `### Run <date>` block, and dies if the log has no
   `last-completed-phase` (the run is not closed).
2. `auto.py next --log <log>` prints `state=`, `round=`, `action=`, `result_schema=`, and
   state-specific fields (`invariant=`, `invariant_text=`, `files=`, `uncovered=`,
   `failed=`). Do exactly the `action=`, nothing else.
3. `auto.py advance --log <log> --result '<json>'` with a result matching `result_schema=`.
   It validates the result, appends the event and the finding entries and notes to
   `logbook.md`, and moves the machine on. On `status=error` the result was invalid and
   nothing was written: fix the result and advance again.
4. Repeat from 2. At `state=SUMMARY` print the summary (below), then `advance --result '{}'`.
   `state=DONE` ends the run.

The machine reads the invariant texts from `functional-spec.md` itself, logs every finding
(32–35), runs the per-round decision (26, 27, 40), the closing verify, and the safety stop.
`auto.py parse`, `decide`, `summary` and `log.py auto-entry`/`auto-note` still exist but you
do not call them in this loop.

## What each state asks of you

- **INIT**: run every layer's `runner` (from `scan-project.py`). `green`, `red`, or `broken`.
- **STATIC_RUN / DYN_RUN**: launch the agent (templates below). Advance with the report path;
  the machine parses it. A parse error ends the run as a failure.
- **STATIC_CLASSIFY**: judge each uncovered invariant **statically testable** (a test can
  exercise it without the running app) or not (7). Not testable: give the reason (9).
- **ACT_TEST**: coverage-gap cycle. Launch `tdd-red` with the coverage-gap template.
  `already-green`: the behavior exists and the new test passes; skip green and refactor, the
  change is test-only. Genuinely red: the behavior is missing, so launch `tdd-green`, then
  `tdd-refactor`, as in Step 6 of SKILL.md. After each agent run the regression check: all
  runners; any previously passing test now failing is a regression, reported with
  `"regression": true` (39). `fix_id` names the fix; findings fixed together share one.
- **DYN_PREFLIGHT**: Glob `.claude/skills/run-*/SKILL.md`. One recipe: report it
  (`"how": "existing"`). Several: read the Step 3 recipe-selection section of
  `~/.claude/skills/spec-verify-dynamic/SKILL.md` at run time, apply its comparison, pick the
  recommended recipe, report it with `"how": "chosen"` and the reason (21). None:
  `{"recipe": null}`.
- **RECIPE_GEN**: ONE generation agent for the whole run (template below), never overwriting
  an existing recipe (19, 22), never retried. Route (a) `/run-skill-generator` if callable,
  else route (b). Report the recipe and route, or `{"failed": "<why>"}` (20).
- **DEP_GATE**: run the dynamic-verify agent up to the dependency map. If any dependency is
  production or unknown the agent tears the app down through the recipe and exercises
  nothing (23, 24, 43). Report every dependency with its class; local and development
  proceed without the yes/no prompt (25).
- **TRIAGE**: classify each failed invariant into exactly one of `defect`, `flaky`,
  `environment`, `spec-mismatch` (14). Re-running a flaky candidate once is part of the
  triage. Only defects are corrected (15, 16); give the files the finding implicates.
  Spec mismatches are only reported (31).
- **CORRECT**: `tdd-red` writes a test reproducing the observed failure, `tdd-green` fixes
  minimally, scoped to the listed files (30), regression check after each. If no failing test
  can be written, a scoped `claude` agent fixes it: `"route": "fallback"`.
- **SUMMARY**: `next` prints the counts (`tests_added= corrections= skipped=
  skipped_by_reason= regression= dynamic=performed|skipped|not-run dynamic_reason=
  needs_review=`), `stop_reason=`, `open=` and `unverified=` (skipped in dynamic, never passed in any round).
  Print the counts, the open invariants with their status, the unverified ones, whether dynamic ran and why not, any recipe flagged needs-review, any
  regression, the stop reason, and point at `initiatives/<name>/logbook.md` (28, 29, 36).
  Always printed, including after a failure, safety stop, or regression stop.

## Agent prompt templates

Use `subagent_type: "claude"` unless stated. That type has every tool, so each prompt
restates its limits. Fill `<name>`, `<root>`, and `<run-recipe>`.

**Static verify**

> Read `~/.claude/skills/spec-verify-static/SKILL.md` and follow Steps 3–7 for `<name>`,
> with `<root>` as the project root. Write only `initiatives/<name>/verify-static-report.md`.
> Omit the `Next:` line. Do not write any other file, never edit `initiatives/*/logbook.md`,
> do not start or stop services, and do not ask questions.

**Dynamic verify**

> Read `~/.claude/skills/spec-verify-dynamic/SKILL.md` and follow Steps 4–7 for `<name>`.
> The run recipe is already resolved: `<run-recipe>`. Overrides: (1) Print the dependency
> map as the skill describes. If any dependency is production or unknown, tear the app
> down via the recipe, exercise no invariant, write no report, and return exactly
> `gate=blocked deps=<comma-separated dependencies>`. (2) Otherwise do not ask the yes/no
> confirmation; proceed. (3) Run no test suites. Skip reasons must start with one of
> `app did not start`, `feature flag could not be enabled`, `no runtime surface to exercise`;
> put any detail in parentheses after it. (4) Omit the `Next:` line. Write only
> `initiatives/<name>/verify-dynamic-report.md`. Never edit `initiatives/*/logbook.md`, do
> not modify the recipe, and do not ask questions.

**Recipe generation** (once per run)

> No run recipe exists under `.claude/skills/run-*/` for this project. Create one, once;
> never overwrite an existing recipe. Route (a): if `/run-skill-generator` is callable,
> invoke it. Route (b), if it is not callable: launch the app from a clean environment,
> note exactly what worked (commands, port, health check, teardown, flags), and write
> `.claude/skills/run-<name>/SKILL.md` as a run recipe. Write only that file. Never edit
> `initiatives/*/logbook.md`. Report which route you used and the path written, or why both
> routes failed.

**Coverage-gap tdd-red**

> Write ONE test for invariant <N> of `initiatives/<name>/functional-spec.md`: <invariant
> text>. This is a coverage-gap test for behavior that may already exist; an immediate pass
> is expected. Do not run the unexpected-pass/lesson workflow and do not write lesson
> files; report `already-green` if the test passes. If it fails for a real reason, report
> the failure. Write only the test; touch no implementation file. Runner: `<runner>`.

**Correction**

> Failing invariant <N>: <invariant text>. Observed: <observed vs expected from the
> dynamic report>. Triage: implementation defect. For `tdd-red`: write ONE test that
> reproduces this observed failure and confirm it fails. For `tdd-green`: make that test
> pass with the minimum change. Touch only these files: <files the finding implicates>.
> No refactors, no unrelated changes, never edit specs or `initiatives/*/logbook.md`.
> Runner: `<runner>`.
>
> Fallback only, if no failing test can be written: a scoped `claude` agent fixes the
> defect in those files only, runs the runner, and reports why no test was possible.
