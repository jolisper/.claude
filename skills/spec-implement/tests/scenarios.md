# `/spec-implement --auto` scenario runbook

Manual runbook for the LLM-executed orchestration of auto mode (`references/auto-mode.md`).
The orchestrator is a driver loop: `auto.py next` says what to do, `auto.py advance --result <json>`
validates the result and writes the logbook. The control flow (state machine in `machine.py`),
the per-round decision, and the logbook lines are covered by pytest; run those first from the repo root:

```
pytest skills/spec-implement/tests
```

Run each scenario by hand against a throwaway fixture initiative in a scratch git repo, so `git status` and `git diff --stat` isolate what the run changed. Assertion surface: `initiatives/<name>/logbook.md` plus `git status`. Before each run, record spec hashes and commit or stash everything else:

```
shasum initiatives/<name>/functional-spec.md initiatives/<name>/technical-spec.md > /tmp/spec.sha
git add -A && git commit -qm "pre-run"
# after the run:
shasum -c /tmp/spec.sha          # must print OK twice
git status --short; git diff --stat
```

## Fixture setup

Scratch repo with a tiny Python CLI/HTTP service, `fixture-svc`, initiative `fixture-svc`:

- `initiatives/fixture-svc/functional-spec.md`: ~6 numbered Behavior invariants, e.g.
  1. `GET /add?a=&b=` returns the sum as JSON. 2. Non-numeric input returns 400. 3. `GET /health` returns 200. 4. Each request is logged to stdout with its status (runtime-only: needs the running app). 5. `PORT` env var selects the port (runtime-only). 6. Results over 1000 return 413.
- `technical-spec.md`: one phase, one module (`app.py`), pytest tests in `tests/`, a `## Testing and validation` section.
- Starting state for most scenarios: `/spec-implement fixture-svc` already ran (logbook has `last-completed-phase`, status complete), tests green, working tree clean. Alternative: start from scratch with `--auto` (then the implementation phases also run before Step 8).
- A run recipe `.claude/skills/run-fixture-svc/SKILL.md` that starts the app on localhost and tears it down. Remove it for D/D1; keep a second one for D2.

Seeding hints per scenario:

| Need | How to seed |
|---|---|
| Testable gap (B) | Delete the test for invariant 6 (413), keep the code. |
| Runtime-only gap (B) | Invariant 4 (stdout logging) has no unit test and cannot be asserted statically. |
| Implementation defect (C) | Break invariant 2 in `app.py` (return 500 instead of 400) and delete or never write its test; runtime check fails. |
| Flaky | Make `/health` fail on the first call only (counter in a temp file). |
| Environment/flag | Invariant 5 depends on a feature flag the recipe cannot enable. |
| Spec mismatch | Spec says 400, code and tests agree on 422 and the spec is the stale side. |
| Production dependency (E) | Recipe points the app at `https://api.prod.example.com` (or a prod DB URL in `.env`). |
| Broken runner (F) | Add a syntax error to a test file, or put a non-existent path in the runner config. |
| Regression (G) | Seed a defect whose obvious fix contradicts an old passing test (e.g. old test pins the buggy value of an unrelated invariant). |
| Persistent defect (J) | Defect whose fix needs a change outside the implicated files (scope forbids it), so it fails in both rounds. |

## Line shapes (from `speclog.format_entry`, `machine.py`)

```
## Auto verification            (first run only)
### Run 2026-11-14
Bound: up to 2 rounds
- [r1] event: STATIC_RUN {"covered": [...], "report": "...", "uncovered": [4, 6]}
- [r1/static] inv 6: <spec text> — acted: coverage-gap test (already-green) [action: test] [fix: t6] [files: tests/test_app.py]
- [r1/static] inv 4: <spec text> — skipped: deferred to dynamic
- [r1] note: defer detail inv 4: <why>
- [r1/dynamic] inv 2: <spec text> — acted: implementation defect corrected (tdd) [action: correction] [fix: f2] [files: app.py, tests/test_app.py]
- [r1/dynamic] inv 5: <spec text> — skipped: <flaky|environment|spec-mismatch>: <evidence>
- [r1/dynamic] inv 3: <spec text> — skipped: no runtime surface to exercise
- [r1] note: skip detail inv 3: <detail>
- [r2/dynamic] inv 2: <spec text> — verified: re-verified after correction: pass
- [r2/dynamic] inv 2: <spec text> — skipped: closing verify: not acted on
- [r1] note: <text>
```

Every transition adds one `event:` line (the machine's memory, replayed to rebuild state); entry text comes from `functional-spec.md`. Dynamic skip reasons are a closed set (`app did not start`, `feature flag could not be enabled`, `no runtime surface to exercise`, else `other`), detail goes in a note. Order of suffixes: `[action: …]`, `[fix: id]`, `[files: a, b]`, `[regression]`. Skips carry no `[action]`.

## Scenarios

### A. Opt-in and flag handling

- **Goal**: default path unchanged; `--auto` announces itself.
- **Setup**: closed fixture initiative.
- **Command 1**: `/spec-implement fixture-svc` (no flag). **Command 2**: `/spec-implement --auto fixture-svc`, and again `/spec-implement fixture-svc --auto` and `/spec-implement initiatives/fixture-svc/technical-spec.md --auto`.
- **Expected logbook**: Command 1: no `## Auto verification` section. Commands 2: section plus `### Run`, `Bound: up to 2 rounds` and an `event: INIT` line.
- **Expected stdout**: Command 1: no verify agent invoked, ends with `Next: /spec-verify-static fixture-svc, …`. Command 2: first line `Auto mode active — up to 2 verify → act rounds.`, no `Next:` line, final summary pointing at `initiatives/fixture-svc/logbook.md`.
- **Expected git**: after Command 1, `git diff --stat -- skills/spec-verify-static skills/spec-verify-dynamic` empty (also empty after every scenario).
- **Verifies**: 3, 4, 5, 41 (1, 2 also in pytest).

### B. One testable gap, one runtime-only gap

- **Goal**: test added for the testable gap only; runtime gap deferred; static re-run.
- **Setup**: seeds "testable gap" (inv 6) and "runtime-only gap" (inv 4). Note `ls ~/.claude/tdd/lessons/` (and its hash: `find ~/.claude/tdd/lessons -type f | sort | xargs shasum`).
- **Command**: `/spec-implement fixture-svc --auto`
- **Expected logbook**:
  ```
  - [r1/static] inv 6: <text> — acted: coverage-gap test (already-green) [action: test] [fix: …] [files: tests/test_app.py]
  - [r1/static] inv 4: <text> — skipped: deferred to dynamic
  ```
  plus a `defer detail inv 4: <why>` note.
  Exactly one entry per finding; static re-run happens after the test (verify-static-report.md rewritten, later mtime than the test file); invariant 4 then exercised dynamically (pass, no entry).
- **Expected stdout**: summary with tests_added 1, corrections 0, skipped 1 (`deferred to dynamic`), dynamic performed, open list, pointer to the logbook.
- **Expected git**: only `tests/test_app.py` modified (plus report files in `initiatives/`); no implementation file changed; no new files under `~/.claude/tdd/lessons/` (the `already-green` override held).
- **Verifies**: 6–11, 28, 30, 36 (also 12, 13).

### C. Implementation defect corrected; non-defects left alone

- **C1: defect**. Seed "implementation defect" (inv 2). Command as B.
  - Expected logbook: `- [r1/dynamic] inv 2: <text> — acted: implementation defect corrected (tdd) [action: correction] [fix: …] [files: app.py, tests/test_app.py]`; then `r2` `event: STATIC_RUN` (static re-run first), then `r2` dynamic passes and `- [r2/dynamic] inv 2: <text> — verified: re-verified after correction: pass`.
  - Order check: in `verify-*-report.md` mtimes and logbook, the r2 static stage precedes the r2 dynamic stage.
  - Git: diff limited to files named in the entry; the new test reproduces the failure (fails on pre-run code: `git stash` the fix to confirm).
- **C2: flaky / environment / spec mismatch** (one fixture each, run separately). Expected logbook: `- [r1/dynamic] inv N: <text> — skipped: flaky|environment|spec-mismatch: <evidence>`. No `[action:]`, no `[files:]`.
  - Git: `git diff --stat` shows no code change; `shasum -c /tmp/spec.sha` OK (specs untouched, including the spec-mismatch case, which is only reported).
- **Expected stdout**: summary with corrections 1 (C1) or 0 (C2), skipped by reason, open list.
- **Verifies**: 12–18, 30, 31, 44 (every changed file in `git status` appears in some `files:`).

### D. No recipe, `/run-skill-generator` not callable (fallback)

- **Goal**: single generation attempt; route recorded; dynamic then runs.
- **Setup**: delete `.claude/skills/run-*`. Closed fixture.
- **Command**: `/spec-implement fixture-svc --auto`
- **Expected logbook**: `event: DYN_PREFLIGHT {"recipe": null}`, `event: RECIPE_GEN {...}` and `- [r1] note: recipe fixture-svc auto-generated, needs review (route: b)` (route `a` if the command was callable; record which, this settles callability). Dynamic follows.
- **Expected stdout**: summary flags the recipe as needs-review (`needs_review=` non-empty).
- **Expected git**: only `.claude/skills/run-fixture-svc/SKILL.md` new (untracked) besides reports; generation attempted exactly once (one note, no retry in round 2).
- **Verifies**: 19, 22 (and 20's inverse).

### D1. Both generation routes fail

- **Setup**: as D, but make the app unstartable (e.g. rename `app.py` entry point, break `requirements`), so route (b) cannot produce a working recipe.
- **Expected logbook**: `event: RECIPE_GEN {"failed": "<why>"}` and `- [r1] note: dynamic skipped: no recipe could be generated: <why>`; no `dynamic` stage entries and no second `RECIPE_GEN` in round 2.
- **Expected stdout**: summary says dynamic not performed and why (`dynamic=skipped dynamic_reason=…`); static results still reported.
- **Expected git**: no code change besides static-pass tests, if any; no half-written recipe left that claims success.
- **Verifies**: 20, 22, 28.

### D2. Two recipes

- **Setup**: `.claude/skills/run-fixture-svc/SKILL.md` and `.claude/skills/run-fixture-svc-docker/SKILL.md`. Hash both.
- **Expected logbook**: `event: DYN_PREFLIGHT {"how": "chosen", ...}` and exactly one `- [r1] note: recipe <name> chosen: <reason>`.
- **Expected stdout**: no prompt about which recipe; run proceeds to dynamic.
- **Expected git**: both recipe hashes unchanged (`shasum` before/after); no new recipe.
- **Verifies**: 21, 22.

### E. Production dependency safety stop

- **Setup**: recipe/app wired to `https://api.prod.example.com`.
- **Expected logbook**: `- [r1] note: safety stop: blocked on <deps>` naming the offending dependency, before any `[r1/dynamic]` entry; no `acted` correction entries.
- **Expected stdout**: dependency map printed; summary reports safety stop, dynamic not exercised, pointer to logbook. No `yes/no` prompt.
- **Expected git**: `git status` shows no source/test change from dynamic stage (static-stage tests from B-like gaps may exist); app torn down (`lsof -i :<port>` empty); no request reached the prod URL.
- **Verifies**: 23, 24, 25 (local deps proceed with no prompt, seen in B–D), 28, 43.

### F. Baseline red

- **Setup**: break the test runner (see seeding table).
- **Expected logbook**: `event: INIT {"baseline": "red"}` and `- [r1] note: delegated-step failure: baseline red`, nothing else in the run block; summary stop reason `failure`.
- **Expected stdout**: stops with the error and what was done so far; no static/dynamic agents launched.
- **Expected git**: no changes (aside from the seed).
- **Verifies**: 37.

### G. Regression

- **Setup**: seed from the table (agent's change fails an old test).
- **Expected logbook**: an entry with the `[regression]` suffix, e.g. `- [r1/dynamic] inv 2: <text> — acted: <reason> [action: correction] [files: app.py] [regression]`, followed by `- [r1] note: regression after the correction for inv N` (or `…the test for inv N`). No `r2` entries.
- **Expected stdout**: summary reports the regression and that the loop stopped (`regression=` set).
- **Expected git**: the offending change is visible in `git diff` (not silently reverted); named in `files:`.
- **Verifies**: 39, 28, 44.

### H. Interruption mid-run

- **Setup**: closed fixture, `--auto`. Kill the session (close terminal / `kill`) after the first `auto-entry` appears in the logbook, between entries.
- **Check**: `python3 ~/.claude/skills/spec-implement/scripts/log.py status --log initiatives/fixture-svc/logbook.md` prints `kind=session`; logbook parses (no truncated line, no `.tmp` file left that replaced it); existing implementation sections byte-identical to the pre-run copy (`diff` against a saved copy up to `## Auto verification`).
- **Then**: `/spec-implement fixture-svc` shows the resume menu.
- **Verifies**: 34, 38.

### I. Clean round 1

- **Setup**: fully covered fixture (all invariants have tests, app correct, recipe present).
- **Expected logbook**: `## Auto verification`, `### Run`, `Bound:`, `event:` lines and no finding entries (or only recipe notes).
- **Expected stdout**: first line `Auto mode active — …`; ends after round 1 (`reason=clean`); summary: 0 tests, 0 corrections, nothing open, says so.
- **Expected git**: clean apart from reports.
- **Verifies**: 10, 28, 40.

### J. Bound reached with a persistent defect

- **Setup**: persistent-defect seed (fails in rounds 1 and 2).
- **Expected logbook**: `r1` acted entry, `r2` entry for the recurrence (labeled `r2`, new line, r1 line untouched), then closing verify findings as
  `- [r2/static|dynamic] inv N: <text> — skipped: closing verify: not acted on`.
- **Expected stdout**: stop reason `bound`; summary lists open invariants with status, and the final state reflects the closing verify.
- **Expected git**: no actions after round 2; diff limited to `files:` entries.
- **Verifies**: 26, 29, 33.

## Final checklist

| Inv | Verified by | Inv | Verified by |
|---|---|---|---|
| 1, 2 | pytest `test_resolve_spec` (also A) | 24 | E |
| 3 | A (and `rounds=2` in `test_resolve_spec`) | 25 | B–D (no prompt on local deps), E |
| 4, 5, 41 | A (no `--auto`, `git diff` on spec-verify-*) | 26 | pytest `test_auto_decide`; J |
| 6, 7, 8, 9, 10, 11 | `test_auto_parse`; B | 27 | pytest `test_auto_decide` |
| 12, 13 | C, B; `test_auto_parse` | 28 | pytest `test_auto_summary`; B–G, I |
| 14, 15, 16 | C1, C2 | 29 | pytest `test_auto_summary`; J |
| 17 | `test_auto_parse`; C | 30, 31 | B, C (diff vs `files:`, spec hashes) |
| 18 | C1 | 32 | pytest `test_log_auto`; B–C |
| 19 | D | 33 | pytest `test_log_auto`; J |
| 20 | D1 | 34, 35 | pytest `test_log_auto`; H |
| 21 | D2 | 36 | pytest `test_auto_summary`; B–E |
| 22 | D, D1, D2 | 37 | F |
| 23 | E | 38 | pytest `test_log_auto` (status); H |
| 39 | G | 40 | pytest `test_auto_decide`; I |
| 42 | scenario transcripts: no orchestrator Write/Edit outside the logbook | 43 | E |
| 44 | scenario assertion: every changed file appears in a `files:` field (C, G) | | |

pytest-only (no scenario): 1, 2, 26, 27, 28, 29, 32–36 at script level. Hand-only: 14–16, 18–25, 30, 31, 37, 39, 42, 43.

## Known gaps

- **(a) Closing-verify key collision.** Closing-verify entries share the (round, stage, invariant) idempotency key with earlier entries of the same round, so `advance` drops a closing-verify line for a finding already logged in that round. Watch for this in J.
- **(b) Not enforced by the machine.** Invariant 30 (actions limited to the implicated files): only spec files are rejected in `files`. The orchestrator can still ignore `next`.
- **(c) `/run-skill-generator` callability** is unverified until scenario D runs; the route recorded in the note (a or b) is the answer.
