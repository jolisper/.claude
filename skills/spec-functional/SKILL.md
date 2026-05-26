---
name: spec-functional
description: >
  Write a FUNCTIONAL.md behavioral spec for a feature from the consumer's perspective.
  Use when the user asks for a functional spec, PRD, behavior doc, FUNCTIONAL.md, or wants
  to define what a feature should do before implementation. Always run before spec-technical —
  FUNCTIONAL.md is the required input for the technical plan.
disable-model-invocation: true
argument-hint: "<definition>"
allowed-tools: Read Glob Grep AskUserQuestion Write Bash(git rev-parse:*)
when_to_use: >
  Invoke when the user asks for a functional spec, PRD, behavioral contract, FUNCTIONAL.md,
  or wants to define feature behavior before writing code. Also invoke when the user
  has a feature description that needs to be formalized as a numbered, testable spec.
  Run this skill first — spec-technical requires FUNCTIONAL.md to exist.
effort: high
---

Write a `FUNCTIONAL.md` behavioral spec for a feature. The functional spec defines what the
consumer observes, what invariants hold, and what edge cases must be handled — with no
implementation details. It is the source of truth for what the feature does.

## Steps

**Step 1 — Accept the definition**

`$ARGUMENTS` is the definition — the user's starting description of the feature. Accept
any form: a sentence, a paragraph, bullet points, links to documents, pasted requirements.
If `$ARGUMENTS` is empty, ask:

```
What feature or behavior should this spec define?
```

If the definition contains file paths or URLs to reference material, read them before
proceeding.

**Step 2 — Resolve the project root**

Run `git rev-parse --show-toplevel` to find the project root. All file paths in this
skill are relative to it. If the command fails (not a git repo), use the current working
directory as the project root and note it in the output.

**Step 3 — Derive the spec identifier**

Suggest a kebab-case `<id>` derived from the definition (e.g. "inline table rendering
in block output" → `inline-table-rendering`). A ticket number (e.g. `APP-1234`,
`GH-567`) is also valid. Present the suggestion and ask for confirmation:

```
Spec directory: specs/inline-table-rendering/
Use this name, or enter a different one (ticket number or kebab-case):
```

Use whatever the user confirms as `<id>`.

**Step 4 — Gather remaining context**

Using the definition as a starting point, identify what is still needed before drafting.
Ask only for what cannot be inferred from the definition — in a single `AskUserQuestion`
call covering all gaps:

- **Consumer type** — who interacts with this surface (end user, API caller, CLI user,
  data model consumer). Infer from the definition when possible; ask only if ambiguous.
- **Key behaviors** — what the feature must do. Extract from the definition first; ask
  only to fill genuine gaps.
- **Known edge cases** — ask if the definition is sparse; users often have specific
  failure modes in mind.

Do not ask for information already present in the definition. One question covering all
gaps is better than several sequential questions.

Each question in the `AskUserQuestion` call must have at least 2 distinct options.
Do not include preamble or summary entries — every entry must be a real question.

**Step 5 — Ask about design mockups (UI features only)**

If the feature has visual interaction or UI states, ask:

```
Does a design mockup exist for this feature?
(a) Yes — provide a link or file path
(b) No
```

- On (a): include the link or path in the spec under `## Design`.
- On (b): note `Design: none provided` in the spec.
- If the feature is purely non-visual (data model, API, CLI without interactive output):
  skip this step entirely.

**Step 6 — Check for an existing spec**

Read `<project-root>/specs/<id>/FUNCTIONAL.md`. If it exists, ask:

```
specs/<id>/FUNCTIONAL.md already exists. How do you want to proceed?
(a) Overwrite with a new spec
(b) Cancel
```

On (b): stop.

**Step 7 — Draft and write FUNCTIONAL.md**

Draft the full spec — do not ask questions during this step. Everything needed was
gathered in Steps 1–5. Write in one pass.

Write to `<project-root>/specs/<id>/FUNCTIONAL.md`. Create the directory if it does not
exist.

If the Write fails: report the error and print the full drafted content to the
conversation so nothing is lost.

## FUNCTIONAL.md structure

**Required sections:**

1. **Summary** — 1–3 sentences: feature name, desired outcome, consumer type.
2. **Behavior** — Numbered list of testable invariants. See "The Behavior section."

**Optional sections** — include only when they add signal; omit the heading if empty:

- **Problem** — Only when the motivation is not obvious from Summary.
- **Goals / Non-goals** — Only when scope is ambiguous or contested.
- **Design** — Link or path to mockup, or `Design: none provided` for visual features
  without one. Omit for non-visual features.
- **Open questions** — Prefer `**Open question:** …` inline next to the relevant
  invariant. Use a dedicated section only when multiple unresolved questions need
  collecting.

Do not include Validation, Testing, or Success criteria sections — those belong in
`TECHNICAL.md`.

## The Behavior section

Behavior is the spec. Everything else is framing.

Write Behavior as a numbered list of invariants, not prose. Each invariant must be
independently testable and describe observable behavior from the consumer's perspective.
Together they must be complete: a reader who finishes Behavior has no remaining questions
about what the feature does in any situation.

Cover at minimum:

- **Happy path** — default behavior and the canonical flow.
- **States and transitions** — every state the consumer can observe, and transitions
  between them.
- **Inputs and responses** — all inputs the consumer can provide and what happens for
  each.
- **Empty, error, loading, cancellation** — behavior in each terminal or waiting state.
- **Edge cases** — permission denied, offline, timeouts, races between state changes,
  concurrent instances, stale or missing data, interactions with adjacent features.
- **Invariants that must not regress** — behaviors explicitly non-negotiable.

Length follows the feature. A trivial feature may need a handful of invariants; a
complex one may need many, organized into sub-sections per state or flow. Err toward
one more edge case rather than one fewer.

## Writing guidance

- Concrete, observable behavior over aspirational wording.
- Each invariant describes what the consumer experiences, not what the code does.
- Avoid implementation details unless directly visible to the consumer.
- Each section earns its place; omit rather than pad.
- When updating an existing `FUNCTIONAL.md`: append new invariants at the end — never
  insert mid-list or renumber. `TECHNICAL.md` references invariants by number;
  renumbering silently breaks those references.

## Length heuristic

Keep framing sections thin; let Behavior carry the length.

- Trivial tweak: no spec needed.
- Small feature (one module, few edge cases): ~30–60 total lines.
- Medium feature (cross-module, multiple states): ~80–150 total lines.
- Large feature: longer is fine; most of the length lives in Behavior.

If the same idea appears in both Summary and Behavior, keep it in Behavior and shorten
or omit the framing.
