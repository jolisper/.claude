# Spec Skill Family

**Date:** 2026-05-26
**Status:** Draft v1

---

## Summary

Two skills that introduce a lightweight spec-first workflow to any project:

| Skill | Purpose |
|-------|---------|
| `spec-functional` | Write `FUNCTIONAL.md`: desired behavior from the consumer's perspective, as numbered testable invariants |
| `spec-technical` | Write `TECHNICAL.md`: grounded implementation plan derived from the contract and the current codebase |

The two skills are complementary and sequential. `spec-functional` produces the source of truth for what the feature should do; `spec-technical` consumes it and translates it into a plan grounded in the actual code. Neither skill implements code — they produce the documents that guide implementation.

---

## Context

The existing skill family has no formalized spec workflow. Features are designed inside the conversation, leading to:

- Behavior ambiguity discovered late (during or after implementation)
- No artifact to diff when requirements change
- Reviewers reconstructing intent from code rather than reading a spec
- Agents re-deriving product decisions that were already made

A two-document spec workflow — one for behavior, one for implementation — addresses all of this. The split matters because product decisions (what) and implementation decisions (how) have different authors, different revision cycles, and different audiences. Keeping them in separate files avoids coupling and makes it clear where each kind of decision lives.

The design is generalized from Warp's `write-product-spec` and `write-tech-spec` skills, which established the same two-document pattern for a specific Rust codebase. This family removes all Warp-specific assumptions and adapts the conventions to work in any project.

---

## Design Decisions

### D1 — Behavior is the spec; everything else is framing

`FUNCTIONAL.md` is organized around a numbered list of testable behavioral invariants, not prose paragraphs or user stories. A reader who finishes the Behavior section should have no remaining questions about what the feature does in any situation. All other sections (Summary, Goals, Problem) exist only to frame the Behavior — if they repeat it or add no signal, they are omitted.

Consequence: the length of `FUNCTIONAL.md` is determined by the number of edge cases the feature has, not by structural overhead.

### D2 — "Consumer" rather than "user"

The surface defined in `FUNCTIONAL.md` may be consumed by a human, by client code, by other services, or by CLI users. The skill uses the word "consumer" to make this explicit and prevent contracts from implicitly assuming a human end user when the surface is an API or data model. The generalization matters: the same writing discipline applies regardless of surface type.

### D3 — Sequential: spec-functional precedes spec-technical

`spec-technical` explicitly depends on `FUNCTIONAL.md`. It reads the contract, resolves numbered Behavior invariants by reference, and maps each one to a test or verification step. This coupling is intentional: it prevents implementation plans from diverging from agreed behavior. When no contract exists, `spec-technical` stops and directs the user to run `spec-functional` first.

### D4 — Validation lives in TECHNICAL.md, not FUNCTIONAL.md

`FUNCTIONAL.md` defines testable invariants but does not specify how they are tested. That separation keeps the contract stable when test strategy changes (e.g. adding e2e coverage after initial unit tests). `spec-technical`'s Testing and Validation section is the authoritative testing plan; it references invariant numbers from `FUNCTIONAL.md` rather than restating them.

### D5 — File convention: `specs/<id>/FUNCTIONAL.md` and `specs/<id>/TECHNICAL.md`

`specs/` lives at the project root. Both skills resolve paths relative to the project root, regardless of the current working directory.

`<id>` is either a ticket number (e.g. `APP-1234`, `GH-567`) or a kebab-case feature name (e.g. `inline-table-rendering`). Both skills ask for the identifier when it is not provided. The sibling relationship — same `<id>` directory, distinct filenames — keeps the contract and implementation plan physically paired without conflating them.

`specs/` contains only `<id>`-named directories as direct children. No engineer-named subdirectories.

### D6 — spec-technical researches the codebase before drafting

`spec-technical` runs `Read`, `Glob`, and `Grep` to inspect the relevant code before writing a single line of the spec. It does not guess about module boundaries, types, or patterns. This discipline is non-optional: an implementation plan that describes an architecture the codebase doesn't have is worse than no plan.

### D7 — spec-functional gathers context before writing, not during

`spec-functional` uses `AskUserQuestion` to gather the feature identifier, consumer type, and key behaviors before starting to draft. It does not produce a partial spec and then ask clarifying questions inline. The goal is a draft that is complete in one pass, not a first draft that requires multiple correction rounds.

Exception: design mockups. The skill asks whether a mockup exists before drafting the Behavior section for any feature with UI or interaction design. Including the link at that point prevents the Behavior section from guessing at intent the designer already settled.

### D8 — Design section only for visual surfaces

The Design section is skipped entirely for non-visual features (data models, APIs, CLI tools without interactive output). For features where a mockup would normally exist, an explicit `Design: none provided` is preferable to silence — so it is clear the absence was acknowledged.

### D9 — Specs are living documents; keep them current

Specs are not frozen once written. When implementation reveals that behavior or a module boundary needs to change, update the spec to reflect what was actually built. The checked-in spec describes what shipped, not the original plan.

---

## Skill: `spec-functional`

**Invocation:** `/spec-functional <definition>`
**Argument hint:** `<definition>`
**Model-invocable:** `false`
**disable-model-invocation:** `true`
**Allowed tools:**
```
Read
Glob
Grep
AskUserQuestion
Write
```

---

### Overview

Write a `FUNCTIONAL.md` that makes the desired behavior of a feature unambiguous enough that an agent can implement it correctly and avoid regressions. The spec is written from the consumer's perspective — what the consumer sees, does, and experiences, and the invariants they can rely on. No implementation details.

The primary input is `$ARGUMENTS` — the **definition**: the user's starting description of the feature. It can be a short phrase, a paragraph, a list of requirements, links to related documents, pasted content from another tool, or any mix. It does not need to be complete or structured. The skill uses it as a seed to draft the full spec, filling gaps by reading linked documents and asking targeted questions.

The directory name used to store the spec (`<id>`) is derived from the definition or asked for separately. It is never part of the raw argument string.

"Consumer" means whoever interacts with the surface:

- For UI features: the end user.
- For an API, protocol, or library: callers — other services, client code, or agents.
- For a CLI tool: the developer invoking it.
- For a data model: code that reads and writes that model.

---

### Protocol

**Step 1 — Accept the definition**

`$ARGUMENTS` is the definition. If `$ARGUMENTS` is empty, ask:

```
What feature or behavior should this spec define?
```

Accept any form: a sentence, a paragraph, bullet points, a link to a document, pasted requirements. If the definition contains links or file paths to reference material, read them before proceeding.

**Step 2 — Derive the spec identifier**

Suggest a kebab-case `<id>` derived from the definition (e.g. definition "inline table rendering in block output" → `inline-table-rendering`). Present it and ask for confirmation or a correction:

```
Spec directory: specs/inline-table-rendering/
Use this name, or enter a different one (ticket number or kebab-case):
```

A ticket number (e.g. `APP-1234`, `GH-567`) is also valid. Use whatever the user confirms as `<id>`.

**Step 3 — Gather remaining context**

Using the definition as a starting point, identify what is still needed before drafting. Ask only for what cannot be inferred from the definition:

- **Consumer type** — who consumes this surface. Often inferrable from the definition; only ask if genuinely ambiguous.
- **Key behaviors** — what the feature must do. Extract these from the definition first; ask only to fill gaps or confirm understanding.
- **Known edge cases** — optional, but ask if the definition is sparse; users often have specific failure modes in mind.

Do not ask for information already present in the definition. One `AskUserQuestion` call covering all missing fields is preferable to several sequential questions.

**Step 4 — Ask about design mockups (UI features only)**

If the feature has any visual interaction or UI states, ask:

```
Does a design mockup exist for this feature?
```

- If yes: ask for the link or file path and include it in the spec.
- If no: note `Design: none provided` in the spec — explicit absence is better than omission.
- If the feature is purely non-visual (data model, API, CLI without interactive output): skip this step entirely.

**Step 5 — Draft `FUNCTIONAL.md`**

Write to `specs/<id>/FUNCTIONAL.md`. The file must contain:

**Required sections:**

1. **Summary** — 1–3 sentences: feature name, desired outcome, consumer type.
2. **Behavior** — Numbered list of testable invariants. See "The Behavior section" below.

**Optional sections** — include only when they add signal; omit the heading entirely if empty:

- **Problem** — Include only when the motivation is not obvious from Summary.
- **Goals / Non-goals** — Include when scope is ambiguous or contested.
- **Design** — Link or file path to the mockup, or `Design: none provided` for visual features without one. Omit for non-visual features.
- **Open questions** — Prefer `**Open question:** …` inline next to the relevant invariant. Collect here only when multiple unresolved questions exist.

**Do not include** Validation, Testing, or Success criteria sections — those belong in `TECHNICAL.md`.

---

### The Behavior section

Behavior is the spec. Everything else is framing.

Write Behavior as a numbered list of invariants, not prose. Each invariant must be independently testable and must describe observable behavior from the consumer's perspective. Together they must give a complete description: a reader who finishes Behavior has no remaining questions about what the feature does in any situation.

Cover at minimum:

- **Happy path** — default behavior and the canonical user flow.
- **States and transitions** — every state the consumer can observe, and how the feature moves between them.
- **Inputs and responses** — all inputs the consumer can provide and what happens for each.
- **Empty, error, loading, cancellation** — how the feature behaves in each terminal or waiting state.
- **Edge cases** — permission denied, offline, timeouts, races between state changes, concurrent instances, stale or missing data, interactions with adjacent features.
- **Invariants that must not regress** — behaviors that are explicitly non-negotiable.

Length follows the feature, not a structural template. A trivial feature may need a handful of invariants. A complex feature may need many, organized into sub-sections per state or flow. Err toward one more edge case rather than one fewer.

---

### Length heuristic

Everything outside Behavior (Summary, optional sections) should stay thin.

- Trivial fix or narrow tweak: no spec needed.
- Small feature (one module, few edge cases): ~30–60 total lines.
- Medium feature (cross-module, multiple states): ~80–150 total lines.
- Large or behaviorally rich feature: longer is fine; most of the length lives in Behavior.

If the same idea appears in both Summary and Behavior, keep it in Behavior and shorten or omit the framing.

---

### Writing guidance

- Concrete, observable behavior over aspirational wording.
- Each invariant describes what the consumer experiences, not what the code does.
- Avoid implementation details unless they are directly visible to the consumer.
- Each section earns its place; omit rather than pad with boilerplate.
- When updating an existing `FUNCTIONAL.md`, append new invariants at the end — never insert mid-list or renumber. `TECHNICAL.md` references invariants by number; renumbering silently breaks those references.

---

### Keep the spec current

Keep `FUNCTIONAL.md` current as the feature evolves. If user-visible behavior changes during implementation, update the contract to reflect what was actually built.

---

## Skill: `spec-technical`

**Invocation:** `/spec-technical [<id>]`
**Argument hint:** `[<id>]`
**Model-invocable:** `false`
**disable-model-invocation:** `true`
**Allowed tools:**
```
Read
Glob
Grep
AskUserQuestion
Write
```

---

### Overview

Write an `TECHNICAL.md` that translates the contract into a grounded implementation plan: which parts of the codebase change, what new types or interfaces are introduced, how the work is sequenced, and how each behavioral invariant from `FUNCTIONAL.md` will be verified.

---

### Protocol

**Step 1 — Locate the contract**

If `$ARGUMENTS` contains an `<id>`, check for `specs/<id>/FUNCTIONAL.md`. If found, read it. If not found, ask the user for the feature identifier.

If no `FUNCTIONAL.md` exists, stop:

```
No FUNCTIONAL.md found for this feature.
Write the contract first with /spec-functional, then re-run /spec-technical.
```

**Step 2 — Research the codebase**

Use `Glob` to locate source files at the project root. If no source files are found, stop:

```
No codebase found at the project root.
TECHNICAL.md requires an existing codebase to research.
```

Otherwise, read the codebase to understand:

- The relevant modules, files, and entry points for the feature area.
- The types, interfaces, or state structures likely to change.
- The data flow from the consumer surface to the backend and back.
- Existing patterns in the codebase that the implementation should follow.

Use `Read`/`Grep` to inspect key files. Do not guess about existing architecture. Reference specific file paths and line numbers in the spec.

If the feature area is unclear, ask the user which module or directory to start from.

**Step 3 — Draft `TECHNICAL.md`**

Write to `specs/<id>/TECHNICAL.md`. The file must contain:

**Required sections:**

1. **Context** — What's being built, how the current system works in the relevant area, and the most important files with line references. Reference `FUNCTIONAL.md` for user-visible behavior rather than restating it. Combine current-state description and code orientation into one grounded section.

2. **Proposed changes** — The implementation plan: which modules change, new types or APIs or state being introduced, data flow, ownership boundaries, and how the design follows existing patterns. Call out tradeoffs explicitly when more than one reasonable path exists.

3. **Testing and validation** — How the implementation will be verified against the contract. Reference the numbered Behavior invariants from `FUNCTIONAL.md` directly (e.g. "Invariant 4 — tested by…") rather than restating them. Each important invariant maps to a concrete test or verification step. This is the authoritative testing plan; `FUNCTIONAL.md` intentionally has no Validation section.

**Optional sections** — include only when they add signal; omit the heading if empty:

- **End-to-end flow** — Only when tracing the path through the system reveals something the Proposed changes list doesn't.
- **Diagram** — Mermaid diagram when visual form explains faster than prose (data flow, state machine, sequence across layers). One or two focused diagrams; omit decorative ones.
- **Risks and mitigations** — When there are real failure modes, regressions, migration concerns, or rollout hazards.
- **Follow-ups** — Deferred cleanup or future work worth naming.

---

### Length heuristic

- Single-file change with a clear approach: skip or keep under ~40 lines.
- Multi-module change with some ambiguity: ~80–150 lines.
- Large cross-cutting or architecturally novel change: longer when every section earns its place.

If Context and Proposed changes end up describing the same files and state from different angles, collapse them into one section.

---

### Writing guidance

- Ground the plan in actual codebase structure, not hypothetical architecture.
- Prefer concrete implementation guidance over generic design language.
- Reference `FUNCTIONAL.md` for behavior instead of restating it.
- Each section earns its place.

---

### Keep the spec current

Keep `TECHNICAL.md` current as implementation progresses. If module boundaries, sequencing, risks, or validation strategy change, update the plan to reflect what was actually done.

---

## Skill Interaction

```
/spec-functional <definition>
  └─ reads linked documents (if any)
  └─ derives <id>, confirms with user
  └─ gathers remaining context → writes specs/<id>/FUNCTIONAL.md

/spec-technical <id>
  └─ reads specs/<id>/FUNCTIONAL.md
  └─ researches codebase (Read, Glob, Grep)
  └─ writes specs/<id>/TECHNICAL.md
     └─ Testing section references FUNCTIONAL.md invariant numbers directly
```

`spec-functional` has no dependency on `spec-technical` and can be used standalone when only behavior documentation is needed. `spec-technical` depends on a `FUNCTIONAL.md` written by `spec-functional` and always researches the codebase before drafting. The delegation is one-directional.

---

## Implementation Order

| # | Item | Status |
|---|------|--------|
| 1 | **`spec-functional`** — core skill; write and validate against a real feature | ⬜ |
| 2 | **`spec-technical`** — depends on D3 (sequential); write after `spec-functional` is working | ⬜ |
| 3 | **Smoke test** — invoke both skills on an existing feature with a known `FUNCTIONAL.md` to validate references and file location conventions | ⬜ |

---

## Open Questions

None.
