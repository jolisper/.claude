---
name: spec-technical
description: >
  Write a technical-spec.md plan for a feature by researching the codebase and
  translating a functional-spec.md behavioral spec into a grounded implementation plan.
  Use when the user asks for a technical spec, implementation plan, or technical-spec.md.
  Requires a functional-spec.md written by spec-functional — stops if none exists.
disable-model-invocation: true
argument-hint: "[<id>]"
allowed-tools: Read Glob Grep AskUserQuestion Write Bash(git rev-parse:*)
when_to_use: >
  Invoke when the user asks for a technical spec, implementation plan, technical-spec.md,
  or wants to plan the implementation of a feature that already has a functional-spec.md.
  Always run after spec-functional. Stops if no functional-spec.md exists for the given initiative.
effort: high
---

Write a `technical-spec.md` that translates a `functional-spec.md` behavioral spec into
a grounded implementation plan: which parts of the codebase change, what new types or
interfaces are introduced, how the work is sequenced, and how each behavioral invariant
from the functional spec will be verified.

Requires a `functional-spec.md` written by `spec-functional`. Will not proceed without one.

## Steps

**Step 1 — Resolve the project root**

Run `git rev-parse --show-toplevel` to find the project root. All file paths in this
skill are relative to it. If the command fails (not a git repo), use the current working
directory and note it in the output.

**Step 2 — Locate the functional spec**

If `$ARGUMENTS` contains a `<name>`, check for `<project-root>/initiatives/<name>/functional-spec.md`.
If `$ARGUMENTS` is empty, ask:

```
Which initiative do you want to derive a technical plan for?
Enter the initiative name (directory name under initiatives/):
```

Read the functional-spec.md if found. If no functional-spec.md exists for the given name, stop:

```
No functional-spec.md found at initiatives/<name>/functional-spec.md.
Write the functional spec first with /spec-functional, then re-run /spec-technical.
```

**Step 3 — Research the codebase**

Use Glob to locate source files at the project root. If no source files are found, stop:

```
No codebase found at the project root.
technical-spec.md requires an existing codebase to research.
```

Otherwise, read the codebase to understand:

- The relevant modules, files, and entry points for the feature area.
- The types, interfaces, or state structures likely to change.
- The data flow from the consumer surface to the backend and back.
- Existing patterns in the codebase that the implementation should follow.

Use Read and Grep to inspect key files. Do not guess about existing architecture.
Reference specific file paths and line numbers in the plan.

If the feature area is unclear from the functional-spec.md and codebase, ask the user which
module or directory to start from before proceeding.

**Step 4 — Check for an existing plan**

Read `<project-root>/initiatives/<name>/technical-spec.md`. If it exists, ask:

```
initiatives/<name>/technical-spec.md already exists. How do you want to proceed?
(a) Overwrite with a new plan
(b) Cancel
```

On (b): stop.

**Step 5 — Draft and write technical-spec.md**

Draft the full plan — do not ask questions during this step. Everything needed was
gathered in Steps 1–3. Write in one pass.

Write to `<project-root>/initiatives/<name>/technical-spec.md`.

If the Write fails: report the error and print the full drafted content to the
conversation so nothing is lost.

After the write succeeds, output:

```
initiatives/<name>/technical-spec.md written.
Next: /spec-implement <name>
```

## technical-spec.md structure

**Required sections:**

1. **Context** — What's being built, how the current system works in the relevant area,
   and the most important files with line references. Reference `functional-spec.md` for
   consumer-visible behavior rather than restating it. Combine current-state description
   and code orientation into one grounded section.

2. **Proposed changes** — The implementation plan: which modules change, new types or
   APIs or state being introduced, data flow, ownership boundaries, and how the design
   follows existing patterns. Call out tradeoffs explicitly when more than one reasonable
   path exists.

3. **Implementation sequence** — An explicitly ordered, numbered list of phases that
   `spec-implement` consumes directly. Each phase is one line naming the file(s) or output
   it produces, ordered by dependency (scaffolding and schema before the logic that depends
   on them). Keep one phase per cohesive unit of work; do not bury the ordering inside the
   Proposed changes prose. Example:

   ```
   1. package manifest and lockfile
   2. src/ directory layout
   3. src/validation.ts — input validators
   4. src/handlers/tasks.ts — CRUD endpoints
   ```

4. **Testing and validation** — How the implementation will be verified against the
   functional spec. Reference the numbered Behavior invariants from `functional-spec.md`
   directly (e.g. "Invariant 4 — tested by…") rather than restating them. Each important
   invariant maps to a concrete test or verification step. This is the authoritative
   testing plan; `functional-spec.md` intentionally has no Validation section.

**Optional sections** — include only when they add signal; omit the heading if empty:

- **End-to-end flow** — Only when tracing the path through the system reveals something
  the Proposed changes list doesn't.
- **Diagram** — Mermaid diagram when visual form explains faster than prose (data flow,
  state machine, sequence across layers). One or two focused diagrams; omit decorative
  ones.
- **Risks and mitigations** — When there are real failure modes, regressions, migration
  concerns, or rollout hazards.
- **Follow-ups** — Deferred cleanup or future work worth naming.

## Writing guidance

- Ground the plan in actual codebase structure, not hypothetical architecture.
- Prefer concrete implementation guidance over generic design language.
- Reference `functional-spec.md` for behavior instead of restating it.
- `spec-implement` parses the **Implementation sequence** section by name to derive its
  phase plan — keep its heading exact and its list ordered by dependency.
- Each section earns its place; omit rather than pad.

## Length heuristic

- Single-file change with a clear approach: omit optional sections, keep under ~40 lines.
- Multi-module change with some ambiguity: ~80–150 lines.
- Large cross-cutting change: longer when every section earns its place.

If Context and Proposed changes end up describing the same files and state from
different angles, collapse them into one section.
