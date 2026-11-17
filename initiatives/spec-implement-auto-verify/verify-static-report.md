# Static verify report — spec-implement-auto-verify
Date: 2026-11-16

Invariant 1 — `/spec-implement <name> --auto` runs the whole pipeline in one invocation: implementation phases, then static 
  Static: no coverage found (LLM-orchestrated in SKILL.md / auto-mode.md; only the manual runbook tests/scenarios.md)

Invariant 2 — `--auto` is accepted alongside either argument form (`<initiative-name>` or a path to `technical-spec.md`), in
  Static: covered — skills/spec-implement/tests/test_resolve_spec.py:10, :28

Invariant 3 — On start, the user sees a line stating auto mode is active and the retry bound in force.
  Static: no coverage found (banner is SKILL.md prose; only the rounds= emission is tested (test_resolve_spec.py:10))

Invariant 4 — Auto mode adds no new prompts of its own
  Static: covered — skills/spec-implement/tests/test_machine.py:419 (agent question becomes a delegated-step failure; the machine has no prompting state)

Invariant 5 — Standalone `/spec-verify-static` and `/spec-verify-dynamic` behave exactly as before, including their reports 
  Static: no coverage found (standalone spec-verify-* skills are untouched; no test pins them)

Invariant 6 — After the last implementation phase closes, static verification runs automatically over every numbered Behavio
  Static: covered — skills/spec-implement/tests/test_machine.py:99, skills/spec-implement/tests/test_log_auto.py:326 (refuses an unclosed log)

Invariant 7 — Each uncovered invariant is classified as either **statically testable** or **not statically testable** (e.g
  Static: covered — skills/spec-implement/tests/test_machine.py:161

Invariant 8 — A statically testable uncovered invariant gets a new test, written through the same red-green-refactor path as
  Static: covered — skills/spec-implement/tests/test_machine.py:145, :185

Invariant 9 — A not-statically-testable uncovered invariant gets no test; it is deferred to dynamic verification and recorde
  Static: covered — skills/spec-implement/tests/test_machine.py:145

Invariant 10 — Covered invariants cause no action.
  Static: covered — skills/spec-implement/tests/test_machine.py:137, :252

Invariant 11 — After new tests are added, static verification re-runs
  Static: covered — skills/spec-implement/tests/test_machine.py:371

Invariant 12 — Dynamic verification runs automatically after static verification finishes, and produces its usual `verify-dyn
  Static: covered — skills/spec-implement/tests/test_machine.py:137, :267

Invariant 13 — Invariants deferred from static verification are exercised dynamically like any other.
  Static: covered — skills/spec-implement/tests/test_machine.py:371

Invariant 14 — Each failed invariant is triaged into exactly one of: **implementation defect**, **flaky run**, **environment 
  Static: covered — skills/spec-implement/tests/test_machine.py:294, :324

Invariant 15 — Only a failed invariant triaged as an implementation defect is corrected
  Static: covered — skills/spec-implement/tests/test_machine.py:294, :324

Invariant 16 — Flaky, environment/flag, and spec-mismatch failures are reported and never fixed by changing code.
  Static: covered — skills/spec-implement/tests/test_machine.py:324

Invariant 17 — Skipped invariants (no runtime surface, app did not start, flag could not be enabled) cause no action and are 
  Static: covered — skills/spec-implement/tests/test_machine.py:267, :276

Invariant 18 — After a correction, dynamic verification re-runs
  Static: covered — skills/spec-implement/tests/test_machine.py:338, :404

Invariant 19 — If no run recipe exists, auto mode makes a single attempt to generate one via `/run-skill-generator`
  Static: covered — skills/spec-implement/tests/test_machine.py:198, :221

Invariant 20 — If generation fails, or dynamic cannot run for any other reason (app did not start, no recipe even after gener
  Static: covered — skills/spec-implement/tests/test_machine.py:198

Invariant 21 — If several run recipes match, auto mode chooses the best match using the same comparison dynamic verification 
  Static: no coverage found (recipe choice is agent judgment; the machine only records it)

Invariant 22 — Generation is attempted at most once per run, never retried within a round, and never overwrites an existing r
  Static: covered — skills/spec-implement/tests/test_machine.py:198

Invariant 23 — Before exercising any invariant dynamically, the dependency map is shown and classified (local / development /
  Static: covered — skills/spec-implement/tests/test_machine.py:232, :244

Invariant 24 — If any dependency is production or unknown, auto mode stops before the test round, names the offending depende
  Static: covered — skills/spec-implement/tests/test_machine.py:232

Invariant 25 — If all dependencies are local or development, the map is printed and accepted automatically; auto mode does no
  Static: covered — skills/spec-implement/tests/test_machine.py:252

Invariant 26 — Auto mode performs at most 2 rounds of verify → act
  Static: covered — skills/spec-implement/tests/test_speclog.py:9, skills/spec-implement/tests/test_auto_decide.py:60, skills/spec-implement/tests/test_machine.py:338

Invariant 27 — A round that makes no progress — no new test added, no correction made, and no change in the set of uncovered 
  Static: covered — skills/spec-implement/tests/test_auto_decide.py:33, :75, skills/spec-implement/tests/test_machine.py:324

Invariant 28 — When the loop ends for any reason (all clean, bound reached, no progress, safety stop), the run finishes with 
  Static: covered — skills/spec-implement/tests/test_machine.py:252, :232, :419

Invariant 29 — Remaining uncovered or failing invariants after the loop ends are listed in the final summary with their statu
  Static: covered — skills/spec-implement/tests/test_machine.py:324, :338

Invariant 30 — Actions are limited to the findings: no new features, refactors, or changes outside the files a finding implic
  Static: no coverage found (only spec files are rejected in files (test_machine.py:172); scope to implicated files is not enforced)

Invariant 31 — Auto mode never edits `functional-spec.md` or `technical-spec.md`, including for spec-mismatch findings; those
  Static: covered — skills/spec-implement/tests/test_machine.py:172, :324

Invariant 32 — For every finding, `logbook.md` receives exactly one entry stating: the finding (invariant number and text), t
  Static: covered — skills/spec-implement/tests/test_log_auto.py:82, skills/spec-implement/tests/test_machine.py:145

Invariant 33 — A finding that recurs in a later round is logged again for that round, labeled with its round number.
  Static: covered — skills/spec-implement/tests/test_log_auto.py:112, skills/spec-implement/tests/test_machine.py:338

Invariant 34 — Entries are appended in order of occurrence and never rewrite earlier entries or the existing implementation l
  Static: covered — skills/spec-implement/tests/test_log_auto.py:4, :30

Invariant 35 — Each entry that led to a test or correction names the files changed.
  Static: covered — skills/spec-implement/tests/test_log_auto.py:148, skills/spec-implement/tests/test_machine.py:294

Invariant 36 — The final summary points to the logbook and gives counts: tests added, corrections made, findings skipped (by 
  Static: covered — skills/spec-implement/tests/test_auto_summary.py:21, :59, :138

Invariant 37 — If a delegated step fails (agent error, test runner broken, script error), auto mode stops, reports the error 
  Static: covered — skills/spec-implement/tests/test_machine.py:419, :432, :128, skills/spec-implement/tests/test_auto_summary.py:301

Invariant 38 — If the run is interrupted mid-auto, the logbook reflects every decision made so far; a subsequent `/spec-imple
  Static: covered — skills/spec-implement/tests/test_machine.py:444, skills/spec-implement/tests/test_log_auto.py:297

Invariant 39 — A new test or correction that breaks previously passing tests is not left in place silently: it is reported in
  Static: covered — skills/spec-implement/tests/test_machine.py:185, skills/spec-implement/tests/test_log_auto.py:198, skills/spec-implement/tests/test_auto_summary.py:97

Invariant 40 — If every invariant is covered and every dynamic invariant passes in round 1, the run ends after that round wit
  Static: covered — skills/spec-implement/tests/test_auto_decide.py:19, skills/spec-implement/tests/test_machine.py:252

Invariant 41 — Without `--auto`, no verification is run by `spec-implement` and the closing `Next:` pointer is printed as tod
  Static: no coverage found (only the auto=false flag is tested (test_resolve_spec.py:61))

Invariant 42 — The orchestrator itself still writes no source, test, or config files; all changes go through delegated agents
  Static: no coverage found (orchestrator behavior, no automated check)

Invariant 43 — `--auto` never causes the app to be exercised against a production or unknown dependency.
  Static: covered — skills/spec-implement/tests/test_machine.py:232, :244

Invariant 44 — Every action taken in auto mode is traceable to a logbook entry (32).
  Static: covered — skills/spec-implement/tests/test_machine.py:294, :185

44 invariants — 37 covered, 7 uncovered
