---
name: spec-research-end
description: >
  Close the research phase of a spec-workflow initiative: confirm the focus and decisions,
  save the research (same procedure as spec-research-checkpoint), offer approved amendments
  to initiative.md, and mark the phase closed in logbook.md. Requires spec-research-start.
disable-model-invocation: true
argument-hint: "[<topic>]"
allowed-tools: Read Write Edit Bash(git rev-parse:*) Bash(test:*)
when_to_use: >
  Invoke when research opened with spec-research-start reaches a conclusion. Use
  spec-research-checkpoint instead to save progress and keep the phase open.
  spec-functional and spec-technical read the saved files once the phase is closed.
effort: medium
---

Conclude the research: a checkpoint with the focus and decisions confirmed, followed by
amendments to the initiative and closing the phase. The research phase is optional and
bracketed by `spec-research-start` and this skill.

**All prompts use plain text menus — never call AskUserQuestion.**

## Shared procedure

Read `~/.claude/skills/spec-research-checkpoint/SKILL.md`. Its fidelity rules, Steps 1–3,
Step 4 (draft and write), file structure and writing guidance apply here unchanged. This
skill adds a confirmation round before the write and two steps after it. Do not duplicate
that procedure from memory — follow the file.

## Steps

**Steps 1–3 — as in spec-research-checkpoint** (project root, initiative and open-phase
check, topic and existing file).

**Step 4 — Confirm the focus and the decisions**

Relevance is judged against the research Question, so settle it with the user before
writing. In one plain text message, one round:

```
Agenda questions this research addressed: <list from agenda.md, marking which this session answered>
Inferred question for this file: <one sentence>
Decisions I recorded as yours: <list, or "none">
Confirm, or correct the focus, the decisions, or what is out of scope.
```

If a decision's rationale is not in the conversation, add a line asking for it in the same
message. The confirmed focus becomes the **Question** section.

**Step 5 — Draft and write the research file**

Run the checkpoint's Step 4 (draft and write) using the confirmed focus and decisions. Print
its output line but not its "phase still open" wording.

**Step 6 — Propose amendments to the initiative**

The initiative's goals were provisional while research was open. If the findings or the
user's decisions change Problem, Goals, Non-goals, Scope or Open questions (including open
questions the research resolved), list the proposed edits:

```
Proposed changes to initiatives/<name>/initiative.md:
1. Goals: <before> → <after>   (because: <research file section>)
2. Open questions: remove "<question>" (resolved in research/<topic>.md)
(a) Apply all
(b) Apply only some (name the numbers)
(c) Skip — leave initiative.md unchanged
```

Apply only what the user approves, with Edit. Keep the initiative's intent-level voice: no
implementation decisions, technology choices or numbered invariants. If nothing needs to
change, skip this step silently.

**Step 7 — Close the phase**

Edit only the `logbook.md` frontmatter: set `research: closed` and
`research-closed: <YYYY-MM-DD>`. Do not touch any other key or the body.

Output:

```
initiatives/<name>/research/<topic>.md written.
initiative.md: <amended | unchanged>.
Research phase: closed.
Next: /spec-functional initiatives/<name>/initiative.md
```
