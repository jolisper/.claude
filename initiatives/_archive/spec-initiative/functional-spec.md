## Summary

`spec-initiative` creates `initiatives/<name>/initiative.md` — the first step in a deliberate
distillation pipeline that moves from vague intention to concrete technical definition.
Each subsequent stage (functional spec → technical spec → implementation) narrows further;
`initiative.md` captures intent and direction at the highest level of abstraction, before
any behavioral or technical decisions are made. Consumer: a developer starting a new
spec-workflow initiative.

## Behavior

### Document contract

1. `initiative.md` contains these sections in order: **Problem**, **Goals**, **Non-goals**,
   **Scope**. **Open questions** is included only when unresolved questions exist.
2. All sections are free prose or structured lists. No numbered invariants appear anywhere in
   the document — those belong in `functional-spec.md`.
3. **Problem** states the situation or gap that motivates the initiative. It answers "why now"
   and "what breaks or is missing." One to three paragraphs; no solution language.
4. **Goals** lists what the initiative must achieve. Each goal is a declarative statement of
   intent, not an implementation step.
5. **Non-goals** lists explicit scope exclusions — things the initiative will not do. Omitting
   something from Goals is not sufficient; contested or easily-assumed scope must be named here.
6. **Scope** is free prose estimating the affected components, subsystems, or effort. It need
   not be precise — its purpose is to surface hidden dependencies and size the work roughly.
7. **Open questions** lists unresolved decisions or external dependencies that block or affect
   the initiative. Each entry names the question and, if known, who owns the answer. The section
   is omitted entirely when no open questions exist.

### Position in the distillation pipeline

8. `initiative.md` operates at the intent level — "why this work" and "what outcome is wanted,"
   not "what the system does" or "how it is built." It must give `spec-functional` enough
   direction to begin distilling behavioral invariants without pre-answering the behavioral
   questions that stage is designed to surface. Appropriate vagueness is a feature; resolving
   behavioral or technical questions here collapses the pipeline and removes the human judgment
   gates between stages.
9. `initiative.md` must not contain implementation decisions, technology choices, or numbered
   behavioral invariants — those belong in `technical-spec.md` and `functional-spec.md`
   respectively.
