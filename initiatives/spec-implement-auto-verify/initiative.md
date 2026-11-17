# Auto verification mode for spec-implement

## Problem

After `spec-implement` finishes, the user must manually chain `/spec-verify-static` and, once a run recipe exists, `/spec-verify-dynamic`. Each verification surfaces findings — gaps in test coverage (static) and runtime defects (dynamic) — and the user has to read them and decide, case by case, whether a new test or a correction is warranted. For routine findings this is repetitive judgment work that interrupts the flow and delays closing the implementation.

The gap is not the verification itself but the decision loop around it: today there is no way to let the workflow run verification end to end and make the "is this worth acting on?" call on the user's behalf, nor any stated criteria for making that call.

## Goals

- Offer an opt-in auto mode for `spec-implement` that carries an implementation through static and dynamic verification without the user driving each step.
- In auto mode, the workflow decides on its own whether static verification findings justify adding new tests.
- In auto mode, the workflow decides on its own whether dynamic verification findings justify corrections.
- Make the decision criteria explicit and inspectable, so the user can understand and trust why a test or correction was or was not made.
- Leave a record of what auto mode decided and why, so the user can review it afterward.

## Non-goals

- Changing the default (interactive) behavior of `spec-implement` or of the verification skills when run standalone.
- Changing what static or dynamic verification check; only who decides on follow-up action changes.
- Removing human judgment gates elsewhere in the spec workflow (initiative, functional, technical stages).
- Unbounded autonomy: auto mode is not meant to loop indefinitely or make changes beyond the scope of the findings.
- Authoring run recipes for dynamic verification where none exist.

## Scope

Primarily touches `spec-implement`, with dependencies on `spec-verify-static` and `spec-verify-dynamic`, which must be callable in a way that returns findings to the orchestrating skill rather than only to the user. Likely also affects the logbook or other bookkeeping used to record decisions. Effort is moderate: the bulk is defining the decision criteria and the stopping conditions, not the plumbing.

## Open questions

- What criteria decide that a static finding warrants a new test versus being ignored? (owner: user)
  - **Resolved:** an uncovered invariant gets a new test, unless it is judged not statically testable (e.g. needs the running app); those are deferred to dynamic verification.
- What criteria decide that a dynamic finding warrants a correction versus being reported only? (owner: user)
  - **Resolved:** a failed invariant is corrected only after triage confirms a real implementation defect. Flaky runs, environment or flag problems, and spec mismatches are reported, never fixed by changing code.
- How is auto mode activated (flag, argument, prompt choice), and does it cover only verification or the whole implementation? (owner: user)
  - **Resolved:** an `--auto` argument on `spec-implement`, covering the whole run (implementation, static verification, dynamic verification). Default behavior is unchanged.
- What bounds the loop — maximum iterations, or conditions that force a stop and hand control back to the user? (owner: user)
  - **Resolved:** bounded retries (suggested N = 2 rounds of verify → act), with an early stop when a round makes no progress. Exact bound to be fixed in later stages.
- What happens when dynamic verification cannot run (no run recipe)? Skip, stop, or ask? (owner: user)
  - **Resolved:** skip dynamic, finish with static results, and report clearly that dynamic was not performed and why. If the reason is no run recipe, make a single attempt to generate one via `/run-skill-generator` (flagged as auto-generated and needing review); on failure, fall back to skipping. The dependency-map safety gate is kept: auto mode stops if any dependency is production or unknown.
- Where are auto-mode decisions recorded for later review? (owner: user)
  - **Resolved:** in `logbook.md`, one entry per finding (acted or skipped, with reason).
