---
name: spec-research-checkpoint
description: >
  Save the intermediate progress of an open research phase: distill the exploratory
  research in the current conversation into initiatives/<name>/research/<topic>.md
  (source-traced findings, options, dead ends, decisions) and keep the phase open. Cheap
  and safe to repeat; run it before /clear or compaction. Requires spec-research-start.
disable-model-invocation: true
argument-hint: "[<topic>]"
allowed-tools: Read Write Bash(git rev-parse:*) Bash(test:*)
when_to_use: >
  Invoke mid-research to save progress without closing the phase — before /clear, before
  compaction, or at a natural pause. Use spec-research-end to conclude the research.
effort: medium
---

Write the findings of the research done in this conversation so far to
`initiatives/<name>/research/<topic>.md` and leave the phase open. It asks nothing beyond
the topic and the existing-file choice, so it stays cheap. It never edits `initiative.md`
or the phase state. `spec-research-end` runs this same procedure and then closes the phase.

**All prompts use plain text menus — never call AskUserQuestion.**

## Fidelity rules

These override everything else in this skill:

- Every entry under **Findings** must trace to something in this session: a URL fetched, a
  file read, a command output, or a statement by the user. Cite it in the entry with an exact
  location (URL plus section, or `file:line`) and a short verbatim excerpt. Where the claim is
  your own inference from a source, say so instead of quoting.
- Never fill gaps with plausible content. A claim with no source in the session goes under
  **Open questions**, not Findings.
- Decisions made by the user during the research are recorded as the user's
  ("Decision (user): ..." with the rationale), not as established facts.
- Tag every technical Finding with its evidence level: `tested` (say what was run, against
  what, and the result), `documented` (from docs or a source), or `inferred` (your own
  reasoning). Never tag something `tested` unless it was actually run in this session or
  the user says it was verified.
- Record dead ends. What was tried and dropped, and why, is as valuable as what was kept.

## Steps

**Step 1 — Resolve the project root**

Run `git rev-parse --show-toplevel`. All paths are relative to it. If the command fails, use
the current working directory and note it.

**Step 2 — Resolve the initiative and check the phase**

The initiative branch is named `<name>`: run `git rev-parse --abbrev-ref HEAD` and check that
`<project-root>/initiatives/<name>/initiative.md` exists. If not, ask
`Which initiative is this research for? (directory name under initiatives/)` and check
again; if still missing, stop and suggest `/spec-initiative` first.

Read `initiative.md`, `research/agenda.md` and the `logbook.md` frontmatter. If `research:`
is not `open`, stop:

```
No open research phase for <name>. Run /spec-research-start first.
```

**Step 3 — Derive the topic and check for an existing file**

`$ARGUMENTS` is the topic, if given. If not and exactly one research file other than
`agenda.md` already exists, default to it. Otherwise suggest a kebab-case topic from the
conversation:

```
Research file: initiatives/<name>/research/<topic>.md
Use this name, or enter a different one (kebab-case):
```

Use whatever the user confirms. Then run
`bash -c "test -f <project-root>/initiatives/<name>/research/<topic>.md && echo exists || echo not-found"`.
If the output is `exists`, read the file, then ask:

```
research/<topic>.md already exists. How do you want to proceed?
(a) Update it — merge what is new from this session
(b) Overwrite it
(c) Cancel
```

On (c): stop. On (a): keep existing entries, add new ones, move items between sections when
this session resolved them (e.g. an Open question that is now a Finding), and update the
`updated` date. Never drop an existing entry without telling the user.

**Step 4 — Draft and write the research file**

The **Question** is the agenda question(s) from `agenda.md` that this session addressed,
or, when `spec-research-end` supplies a confirmed focus, that focus. Include in Findings only
what bears on it. Record only decisions the user stated explicitly in this session, with
rationale if given; do not infer decisions.

Draft in one pass — do not ask questions during this step. Collect Sources from the session:
every URL fetched and every file read that a Finding relies on.

Write to `<project-root>/initiatives/<name>/research/<topic>.md`. If the write fails, report
the error and print the full drafted content so nothing is lost.

Output:

```
initiatives/<name>/research/<topic>.md written (checkpoint; phase still open).
Decisions recorded: <list, or "none">
```

## research/<topic>.md structure

Start with this frontmatter, using today's date for `updated` (and `started` on creation):

```
---
started: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---
```

Then these sections, in order:

**Question** — The focus of the research: the agenda question(s) addressed, or the focus confirmed by `spec-research-end`. One to three sentences.

**Context** — Why the question matters and what was already known at the start. Brief.

**Findings** — What was learned. Each entry is one claim plus its source, e.g.
`- [tested|documented|inferred] <claim> — <URL#section | file:line | "user"> "<short verbatim excerpt>"`.
Algorithms, code snippets and working recipes belong here, in a fenced block under the
entry, with their source. For `tested` entries add the how and the result.

**Options** — The alternatives found, each with its trade-offs. Omit if the research
surfaced no alternatives.

**Rejected / dead ends** — What was tried or considered and dropped, and why. Omit if
none.

**Decisions** — Decisions the user made during the research, each as
`Decision (user): <decision> — because <rationale>`. Omit if none.

**Conclusion** — What the research established, or where it stands if still in progress.
Findings-level: what was learned, not a specification of what to build.

**Open questions** — Unresolved or unsourced items. Each names the question and, if known,
who owns the answer. Omit if none.

**Sources** — Every URL fetched and file read that the Findings rely on.

## Writing guidance

Record what works and how — algorithms, approaches, tested recipes — because later spec
stages build on them. Record the user's decisions as decisions, with rationale, but do not specify what to
build: requirements, behavior and the chosen design belong to the spec-* stages that follow. Keep entries short and
scannable; the file is read by people and by those stages.
