# Functional spec — auto verification mode for spec-implement

## Summary

An opt-in `--auto` argument on `/spec-implement` that carries an implementation through static and dynamic verification and decides, without prompting, whether findings justify new tests or corrections. Consumer: a CLI user running the spec workflow.

## Goals / Non-goals

- Goal: remove the user from the verify → read findings → decide loop for routine findings, with an inspectable record of every decision.
- Non-goal: changing interactive behavior of `spec-implement`, or of `spec-verify-static` / `spec-verify-dynamic` run standalone; changing what either verification checks; unbounded autonomy; authoring run recipes beyond the single attempt in 22.

## Behavior

### Activation and scope

1. `/spec-implement <name> --auto` runs the whole pipeline in one invocation: implementation phases, then static verification, then dynamic verification. Without `--auto`, behavior is identical to today.
2. `--auto` is accepted alongside either argument form (`<initiative-name>` or a path to `technical-spec.md`), in any position.
3. On start, the user sees a line stating auto mode is active and the retry bound in force.
4. Auto mode adds no new prompts of its own. Existing stops (dirty working tree, ambiguous spec, stalled phase, script or agent failure) still apply and still hand control to the user.
5. Standalone `/spec-verify-static` and `/spec-verify-dynamic` behave exactly as before, including their reports and `Next:` pointers.

### Static verification

6. After the last implementation phase closes, static verification runs automatically over every numbered Behavior invariant and produces its usual `verify-static-report.md`.
7. Each uncovered invariant is classified as either **statically testable** or **not statically testable** (e.g. observable only in the running app).
8. A statically testable uncovered invariant gets a new test, written through the same red-green-refactor path as implementation. Test-only: no unrelated code is changed.
9. A not-statically-testable uncovered invariant gets no test; it is deferred to dynamic verification and recorded as deferred.
10. Covered invariants cause no action.
11. After new tests are added, static verification re-runs. A round is one verify → act cycle.

### Dynamic verification

12. Dynamic verification runs automatically after static verification finishes, and produces its usual `verify-dynamic-report.md`.
13. Invariants deferred from static verification are exercised dynamically like any other.
14. Each failed invariant is triaged into exactly one of: **implementation defect**, **flaky run**, **environment or flag problem**, **spec mismatch**.
15. Only a failed invariant triaged as an implementation defect is corrected. The correction is scoped to that finding; unrelated code is not touched.
16. Flaky, environment/flag, and spec-mismatch failures are reported and never fixed by changing code.
17. Skipped invariants (no runtime surface, app did not start, flag could not be enabled) cause no action and are carried into the final report as skipped.
18. After a correction, dynamic verification re-runs. A correction made after a dynamic round triggers a static re-run first, so tests still cover the changed code.

### Dynamic verification cannot run

19. If no run recipe exists, auto mode makes a single attempt to generate one via `/run-skill-generator`. A generated recipe is flagged as auto-generated and needing review, in the log and in the final summary.
20. If generation fails, or dynamic cannot run for any other reason (app did not start, no recipe even after generation), dynamic verification is skipped, the run finishes with static results, and the final summary states that dynamic was not performed and why.
21. If several run recipes match, auto mode chooses the best match using the same comparison dynamic verification already uses, and logs which it chose and why. It does not prompt.
22. Generation is attempted at most once per run, never retried within a round, and never overwrites an existing recipe.

### Dependency safety gate

23. Before exercising any invariant dynamically, the dependency map is shown and classified (local / development / production / unknown) as today.
24. If any dependency is production or unknown, auto mode stops before the test round, names the offending dependencies, and hands control to the user. No invariant is exercised and no correction is made.
25. If all dependencies are local or development, the map is printed and accepted automatically; auto mode does not ask for the yes/no confirmation.

### Bounds and stopping

26. Auto mode performs at most 2 rounds of verify → act. The bound is shown at start (see 3).
27. A round that makes no progress — no new test added, no correction made, and no change in the set of uncovered or failing invariants — ends the loop early without using the remaining rounds.
28. When the loop ends for any reason (all clean, bound reached, no progress, safety stop), the run finishes with a final summary, not silently.
29. Remaining uncovered or failing invariants after the loop ends are listed in the final summary with their status; auto mode does not keep trying.
30. Actions are limited to the findings: no new features, refactors, or changes outside the files a finding implicates.
31. Auto mode never edits `functional-spec.md` or `technical-spec.md`, including for spec-mismatch findings; those are reported only.

### Decision record

32. For every finding, `logbook.md` receives exactly one entry stating: the finding (invariant number and text), the decision (acted or skipped), and the reason.
33. A finding that recurs in a later round is logged again for that round, labeled with its round number.
34. Entries are appended in order of occurrence and never rewrite earlier entries or the existing implementation log sections.
35. Each entry that led to a test or correction names the files changed.
36. The final summary points to the logbook and gives counts: tests added, corrections made, findings skipped (by reason), invariants still uncovered or failing, dynamic skipped or not.

### Failure and interruption

37. If a delegated step fails (agent error, test runner broken, script error), auto mode stops, reports the error and what was already done, and hands control to the user. It does not retry beyond the round bound.
38. If the run is interrupted mid-auto, the logbook reflects every decision made so far; a subsequent `/spec-implement` resume sees a consistent log.
39. A new test or correction that breaks previously passing tests is not left in place silently: it is reported in the final summary and logged as a regression, and the loop stops.
40. If every invariant is covered and every dynamic invariant passes in round 1, the run ends after that round with no tests or corrections and a summary saying so.

### Must not regress

41. Without `--auto`, no verification is run by `spec-implement` and the closing `Next:` pointer is printed as today.
42. The orchestrator itself still writes no source, test, or config files; all changes go through delegated agents.
43. `--auto` never causes the app to be exercised against a production or unknown dependency.
44. Every action taken in auto mode is traceable to a logbook entry (32).
