## Summary

`spec-verify` checks that every numbered Behavior invariant in `functional-spec.md` is satisfied
by the implementation. It runs in two phases — static (test coverage) then dynamic (running app)
— and produces a per-invariant pass/fail report. Consumer: a developer who has completed
`spec-implement` and wants to confirm the implementation matches the functional spec before
archiving.

## Behavior

### Input and prerequisites

1. `$ARGUMENTS` is the initiative name (e.g. `my-feature`). If empty, the skill asks:
   ```
   Which initiative should be verified? (kebab-case name):
   ```
2. Before proceeding, the skill checks that all three prerequisites exist:
   - `initiatives/<name>/functional-spec.md` — source of invariants
   - `initiatives/<name>/implement-log.md` — implementation context
   - `.claude/skills/run-<name>/` — the run recipe for launching the app
3. If `functional-spec.md` is missing, the skill stops:
   ```
   initiatives/<name>/functional-spec.md not found. Run /spec-functional first.
   ```
4. If `implement-log.md` is missing, the skill stops:
   ```
   initiatives/<name>/implement-log.md not found. Run /spec-implement first.
   ```
5. If the run recipe is missing, the skill stops:
   ```
   .claude/skills/run-<name>/ not found.
   Create a run recipe there with test environment variables and a non-production
   database configured before running spec-verify.
   ```
   The skill does not create the recipe — that is the user's responsibility.

### Invariant extraction

6. The skill reads all numbered Behavior invariants from `functional-spec.md`. It identifies
   invariants as numbered list items under a `## Behavior` heading (or sub-headings within it).
7. If no numbered invariants are found, the skill stops and reports that the functional spec
   has no numbered Behavior invariants to verify.

### Static phase — test coverage

8. For each invariant, the skill reads the test suite files referenced or implied by
   `implement-log.md` and determines whether a test exists that covers that invariant.
9. An invariant is considered statically covered when at least one test case directly
   exercises the behavior the invariant describes.
10. The skill records the result for each invariant: `covered` (with file and line reference)
    or `no coverage found`.

### Dynamic phase — running app

11. The skill launches the app via the run recipe at `.claude/skills/run-<name>/`.
12. If the app fails to start, the skill records all dynamic results as `skip — app did not
    start`, reports the launch error, and proceeds to the report.
13. For each invariant, the skill exercises the running app to observe whether the described
    behavior holds, and records the result as `pass` or `fail — <observed vs expected>`.
14. Dynamic verification is performed against each invariant in order; the skill does not
    skip an invariant because the static phase found no coverage for it.

### Report

15. After both phases complete, the skill produces a per-invariant report in this format:
    ```
    Invariant N — <first line of invariant text>
      Static:  covered — <file>:<line>  |  no coverage found
      Dynamic: pass  |  fail — <what was observed vs expected>  |  skip — app did not start
    ```
16. The report closes with a summary line:
    ```
    <N> invariants total — <P> passed, <F> failed, <S> skipped, <U> uncovered
    ```
    where "uncovered" means static phase found no test and dynamic phase skipped.
17. The report is printed to the conversation; it is not written to disk unless the user
    explicitly asks.

### Edge cases

18. If static and dynamic results conflict (static: covered, dynamic: fail), the report
    surfaces the discrepancy explicitly:
    ```
    Dynamic: fail — tests pass but observed behavior does not match invariant
    ```
19. If `implement-log.md` references no implementation files, the skill proceeds with the
    static phase using the project's full test suite instead, and notes this in the report.
20. Running `spec-verify` multiple times is safe — it is read-only and produces no side effects.
