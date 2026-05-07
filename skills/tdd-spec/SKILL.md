---
name: tdd-spec
description: >
  Write a gap-free spec for /tdd-session from a short-to-medium objective,
  or convert an existing spec into the tdd-spec format.
  Scans the project to infer language, test runner, and structure; asks targeted
  clarifying questions in one batch; then writes a structured spec file ready for
  /tdd-session to consume without ambiguity.
  Invoke before /tdd-session when your objective needs a precise spec first.
disable-model-invocation: true
argument-hint: "<objective or path/to/existing-spec.md>"
when_to_use: "Before /tdd-session when you want to turn a short objective or existing spec into a precise, unambiguous spec file"
effort: high
allowed-tools: Read Glob Grep Bash(mkdir:*) Write AskUserQuestion
---

# TDD Spec Writer

Produce a gap-free spec that `/tdd-session` can consume without ambiguity. The spec
must make `tdd-session` fully self-sufficient: able to identify the core module, derive
every behavior, honor every constraint, and know when implementation is complete —
with no additional user input.

## Step 1 — Parse the input

Resolve `$ARGUMENTS`:

- If empty or whitespace-only, ask: "What do you want to build? Give a brief description." Stop and wait.
- If it looks like a file path (contains `/` or ends in a known extension such as `.md`, `.txt`, `.spec`, `.feature`), use Read to load it. If the file does not exist, tell the user and ask for a description instead. Treat the file contents as the **source spec** — a starting point to convert into a tdd-spec. Note which sections are already present and which are missing or underspecified.
- Otherwise treat `$ARGUMENTS` as the initial objective.

## Step 2 — Scan the project

Use Glob, Read, and Grep to determine:

- **Language and runtime** — look for `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `mix.exs`, `*.gemspec`, etc.
- **Test runner** — look for `jest.config.*`, `vitest.config.*`, `pytest.ini`, `go.sum`, `mix.exs`, `Gemfile`, etc.
- **Module layout** — where source files live, where test files live, naming conventions used.
- **Existing spec directories** — Glob for `specs/`, `spec/`, `tdd/specs/`. Note the path and naming pattern if found.

Do not ask about anything you can determine from the scan.

## Step 3 — Ask (one batch)

Build a numbered question list covering all unknowns. When a source spec was loaded in Step 1, skip any question that is already answered in it — only ask about genuine gaps.

Always ask if not already present:

1. **Exact goal** — Confirm or sharpen the objective in one sentence: what does "done" look like from the caller's perspective?
2. **Public API** — What are the function, class, or method names? What are their parameter types and return types?
3. **Error handling** — What should happen on invalid or edge-case inputs? Which errors or exceptions are expected?
4. **Out of scope** — What must NOT be built? Name at least one explicit exclusion.

Include only if not determinable from the source spec or the project scan:

5. Language or runtime (if ambiguous).
6. Test runner (if not found in config files).
7. Where the new module should live (file path or package name).

If all questions are answered by the source spec and the project scan, skip this step entirely and proceed to Step 4.

Send all questions in a single `AskUserQuestion` call. Never ask one question at a time.

## Step 4 — Draft the spec

Read `references/spec-template.md` before drafting. Follow its format exactly.

When converting a source spec: carry over any content that is already well-specified
(goal, constraints, overview). Rewrite or expand any section that would leave
`tdd-session` with ambiguity — particularly behaviors that lack exact function names,
input values, or expected outputs.

Fill every section. Leave no placeholders. If any section cannot be filled after steps 2–3,
ask the user before writing — never produce a spec with gaps.

**The Behaviors section is the most critical output of this skill.** Each entry must:
- Name the exact function or method under test
- Specify exact inputs (concrete values or types)
- State the exact expected output or side effect
- Be a single unambiguous sentence passable directly to `tdd-red` as the behavior to implement

Order behaviors from simplest to most complex: happy path first, edge cases next,
error and rejection cases last.

## Step 5 — Review

Present the full spec inside a fenced markdown code block. Then ask:

```
Here's the spec draft. How do you want to proceed?
(a) Write it as-is
(b) Adjust — tell me what to change
(c) Cancel
```

If (b): apply changes, show the updated draft, and ask again. Repeat until (a) or (c).
On (c): stop without writing anything.

## Step 6 — Write

On (a):

1. Determine output path:
   - If an existing `specs/`, `spec/`, or `tdd/specs/` directory was found in Step 2, follow that directory and naming pattern.
   - Otherwise use `specs/<slug>/spec-<slug>.md` where `<slug>` is a kebab-case summary of the goal.
2. Run `mkdir -p <parent-directory>`.
3. Write the spec to `<path>`.
4. Confirm: "Spec written to `<path>`. Run `/tdd-session <path>` to start implementation."

If any step fails, report which step failed and stop. Do not retry automatically.

## When NOT to use this skill

Abort and tell the user if:
- The objective spans more than one independent module — split into separate specs and invoke once per module.
- The objective requires external hardware, live network APIs, or infrastructure that cannot be unit-tested.
- A spec file already exists in tdd-spec format — skip this skill and run `/tdd-session <path>` directly.
