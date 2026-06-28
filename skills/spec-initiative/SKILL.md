---
name: spec-initiative
description: >
  Create initiatives/<name>/initiative.md — the intent-level anchor for a spec-workflow
  initiative. Use when starting a new initiative, before running spec-functional.
  Accepts a free-form description and produces a structured document covering Problem,
  Goals, Non-goals, and Scope.
disable-model-invocation: true
argument-hint: "<description>"
allowed-tools: Read Write Bash(git rev-parse:*)
when_to_use: >
  Invoke when the user wants to start a new initiative, capture the "why" behind upcoming
  work, or create the upstream document that feeds into spec-functional. Run this skill
  first — initiative.md is the input to spec-functional.
effort: high
---

Create `initiatives/<name>/initiative.md` — the first step in the spec-workflow distillation
pipeline. This document operates at the intent level: it captures why the work exists and what
outcome is wanted, before any behavioral or technical decisions are made.

**All prompts use plain text menus — never call AskUserQuestion.**

## Steps

**Step 1 — Accept the description**

`$ARGUMENTS` is the initiative description. Accept any form: a sentence, a paragraph,
bullet points, pasted notes.

If `$ARGUMENTS` is empty, ask:

```
What is this initiative about? Give me a short description.
```

If `$ARGUMENTS` contains a file path, read it and treat its content as the description.
If `$ARGUMENTS` contains a URL, fetch it and treat the content as the description.

**Step 2 — Resolve the project root**

Run `git rev-parse --show-toplevel` to find the project root. All file paths are relative
to it. If the command fails, use the current working directory and note it.

**Step 3 — Derive the initiative name**

Suggest a kebab-case `<name>` derived from the description. Present the suggestion:

```
Initiative directory: initiatives/<name>/
Use this name, or enter a different one (kebab-case):
```

Use whatever the user confirms as `<name>`.

**Step 4 — Gather remaining context**

Identify what's still needed to draft a complete `initiative.md`. Ask only for what cannot
be inferred from the description — in a single plain text message covering all gaps:

- **Scope boundaries** — what components or areas are in or out of scope?
- **Non-goals** — explicit exclusions the user has in mind?
- **Open questions** — known unknowns or blockers to capture?

If the description is detailed enough to draft all sections without ambiguity, skip this step.

Never ask more than one round.

**Step 5 — Check for an existing initiative**

Read `<project-root>/initiatives/<name>/initiative.md`. If it exists, ask:

```
initiatives/<name>/initiative.md already exists. How do you want to proceed?
(a) Overwrite with a new initiative doc
(b) Cancel
```

On (b): stop.

**Step 6 — Draft and write**

Draft the document in one pass — do not ask questions during this step.

Write to `<project-root>/initiatives/<name>/initiative.md`, creating the directory if needed.

If the Write fails: report the error and print the full drafted content to the conversation
so nothing is lost.

Also write `<project-root>/initiatives/<name>/logbook.md` with this content, using today's
date for `started`:

```
---
status: in-progress
started: <YYYY-MM-DD>
---
```

After both writes succeed, output:

```
initiatives/<name>/initiative.md written.
initiatives/<name>/logbook.md created.
Next: /spec-functional initiatives/<name>/initiative.md
```

## initiative.md structure

Write these sections in order. All content is free prose or structured lists — no numbered
invariants anywhere in the document.

**Problem** — The situation or gap that motivates this initiative. Answers "why now" and
"what is missing or broken." One to three paragraphs. No solution language.

**Goals** — What the initiative must achieve. Each goal is a declarative statement of
intent, not an implementation step.

**Non-goals** — Explicit scope exclusions. Omitting something from Goals is not sufficient;
contested or easily-assumed scope must be named here.

**Scope** — Free prose estimating affected components, subsystems, or effort. Need not be
precise — its purpose is to surface hidden dependencies and size the work roughly.

**Open questions** — Unresolved decisions or external dependencies. Each entry names the
question and, if known, who owns the answer. Omit this section entirely if no open
questions exist.

## Writing guidance

Stay at the intent level. This document answers "why this work" and "what outcome is
wanted" — not "what the system does" or "how it is built." Appropriate vagueness is a
feature: resolving behavioral or technical questions here short-circuits the stages designed
to do that work and removes the human judgment gates between them.

Do not include implementation decisions, technology choices, or numbered behavioral
invariants — those belong in later stages.
