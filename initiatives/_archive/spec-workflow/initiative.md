# Initiative: spec-workflow

## Problem

The spec-* skill family covers Specification → Implementation well, but the workflow has no defined entry point and no exit. There is no upstream "why" document to anchor the work, no verification step to confirm the implementation satisfies the functional spec, and no archiving step to close out a completed initiative. The pipeline is also undiscoverable — skills must be chained manually with no shared convention tying them together.

## Goals

- Add a structured but free-form initiative document as the first step in the workflow.
- Extend the spec-* family to cover the full lifecycle: Initiative → Specification → Implementation → Verification → Archive.
- Keep each skill's responsibility narrow; do not collapse steps that require separate human judgment.

## Non-goals

- Automating the transition between stages — each step remains explicitly user-invoked.
- Replacing or rewriting existing spec-functional, spec-technical, or spec-implement skills.
- Adding a "generate both specs from initiative" shortcut skill — functional and technical specs require separate review and codebase research.

## Proposed workflow

```
/spec-initiative   →  initiatives/<name>/initiative.md
/spec-functional   →  initiatives/<name>/functional-spec.md   (auto-reads initiative.md)
/spec-technical    →  initiatives/<name>/technical-spec.md
/spec-implement    →  code + initiatives/<name>/implement-log.md
/spec-verify       →  invariant coverage report
/spec-archive      →  initiatives/_archive/<name>/
```

All files live under `initiatives/<name>/` at the project root, consistent with the existing spec-* convention.

## New skills needed

- **`/spec-initiative`** — Creates `initiative.md`: Problem, Goals, Non-goals, Success criteria, Open questions, rough scope. Free prose, no numbered invariants. Becomes the `$ARGUMENTS` input to `spec-functional`.
- **`/spec-verify`** — Reads `functional-spec.md` invariants and implementation files from `implement-log.md`, verifies each invariant is covered via test suite and code review. Produces a coverage report.
- **`/spec-archive`** — Moves `initiatives/<name>/` to `initiatives/_archive/<name>/`, appends a retrospective note to the implement log, marks status as `archived`.

## Enhancements to existing skills

- **`spec-functional`** — Auto-detect and pre-read `initiative.md` from the same initiative directory when present, so it can be seeded from the initiative without requiring a manual path argument.

## Success criteria

- [ ] `/spec-initiative` creates a well-structured initiative doc and establishes the `initiatives/<name>/` directory.
- [ ] `/spec-functional` reads `initiative.md` automatically when present in the same directory.
- [ ] `/spec-verify` produces a per-invariant coverage report against the functional spec.
- [ ] `/spec-archive` cleanly closes out a completed initiative with a retrospective.
- [ ] The full workflow can be driven end-to-end from a blank slate to archived initiative.

## Scope note

The spec-* family is intentionally biased toward code projects. `spec-technical` researches source code; `spec-implement` drives TDD cycles; `spec-verify` checks test coverage. This is by design — the full pipeline targets software implementations.

For non-code contexts (config directories, skill authoring, prose documents), the intended pattern is to use only the first half of the workflow — `/spec-initiative` and `/spec-functional` — and then pass the resulting `functional-spec.md` directly to `/skill-create` as its file-path argument. `skill-create` already accepts a file path as design context; its Phase 2 clarification fills the gaps the functional spec doesn't cover (target agent, skill name, install scope), and its Phase 4 review is the human judgment gate before anything is written.

## spec-verify behavior

Requires a `/run-skill-generator` recipe to exist at `.claude/skills/run-<name>/` before proceeding — if absent, stops and instructs the user to create one with test environment variables and a non-production database configured. Isolation is the user's responsibility at recipe-creation time; the skill enforces the prerequisite and delegates launch to the recipe.

Once a recipe exists, exercises each numbered Behavior invariant from `functional-spec.md` against the running app and produces a per-invariant pass/fail report.

## spec-archive behavior

Moves `initiatives/<name>/` to `initiatives/_archive/<name>/`. Before moving:

1. **Completeness check** — reads `implement-log.md` frontmatter; if `status` is not `complete`, warns and asks for confirmation before proceeding.
2. **Uncommitted changes check** — if implementation files have unstaged or uncommitted changes, surfaces them and asks for confirmation.
3. **Retrospective note** — auto-generates a closing paragraph from the implement log (phases completed, deviations from spec, lessons) and appends it to `implement-log.md` after user review.
4. **Date stamp** — updates `implement-log.md` frontmatter: `archived: <YYYY-MM-DD>`, `status: archived`.

Then moves the directory.
