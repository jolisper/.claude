---
name: spec-research-start
description: >
  Open the optional research phase of a spec-workflow initiative. Reads initiative.md,
  agrees a research agenda with the user, writes initiatives/<name>/research/agenda.md and
  marks the phase open in logbook.md. Use after spec-initiative when the open questions are
  too large for the codebase alone; close the phase with spec-research-end.
disable-model-invocation: true
argument-hint: "[<initiative-name>]"
allowed-tools: Read Write Edit Bash(git rev-parse:*) Bash(mkdir:*)
when_to_use: >
  Invoke after spec-initiative when the initiative's goals are still provisional and there
  are unknowns to reduce — decisions to make, approaches to test, evidence to gather —
  before specifying behavior. Skip it when the initiative and the codebase are enough.
effort: medium
---

Open the research phase of an initiative. The phase is a stage of the initiative, between
`spec-initiative` and `spec-functional`: the goals are provisional, and the exploration that
follows (free-form, in this conversation) makes decisions and gathers evidence for the
specs. `spec-research-end` closes it. While the phase is open, `spec-functional` and
`spec-technical` refuse to run.

**All prompts use plain text menus — never call AskUserQuestion.**

## Steps

**Step 1 — Resolve the project root**

Run `git rev-parse --show-toplevel`. All paths are relative to it. If the command fails, use
the current working directory and note it.

**Step 2 — Resolve the initiative**

`$ARGUMENTS` is the initiative name, if given. Otherwise the initiative branch is named
`<name>`: run `git rev-parse --abbrev-ref HEAD` and use that. Check that
`<project-root>/initiatives/<name>/initiative.md` and `logbook.md` exist. If not, ask:
`Which initiative is this research for? (directory name under initiatives/)` and check
again; if still missing, stop and suggest `/spec-initiative` first.

Read `initiative.md` and the `logbook.md` frontmatter.

**Step 3 — Check the phase state**

Read the `research:` key in the `logbook.md` frontmatter.

- Absent: continue.
- `open`: ask
  ```
  Research is already open for <name> (since <research-started>). How do you want to proceed?
  (a) Keep it open and revise the agenda
  (b) Cancel
  ```
  On (b): stop.
- `closed`: ask
  ```
  Research was closed on <research-closed>. How do you want to proceed?
  (a) Reopen it and revise the agenda
  (b) Cancel
  ```
  On (b): stop.

**Step 4 — Agree the agenda**

Propose an agenda from the initiative's Open questions and any goal that is still
provisional. In one plain text message, one round:

```
Research agenda for <name>:
1. <question — from Open questions or a provisional goal>
2. ...
Out of scope: <anything the initiative excludes that research should not wander into>

Confirm, or tell me what to add, drop or reword.
```

If the initiative has no Open questions and no provisional goal, ask what the unknowns are
instead of inventing an agenda.

**Step 5 — Write the phase state**

Create `<project-root>/initiatives/<name>/research/` if needed and write `agenda.md` there
(overwriting an earlier one when revising):

```
# Research agenda: <name>

Started: <YYYY-MM-DD>

## Questions

1. <question>

## Out of scope

- <item>
```

Then edit only the `logbook.md` frontmatter: set `research: open` and
`research-started: <YYYY-MM-DD>` (keep an existing `research-started` when revising). Do not
touch any other key or the body — `spec-implement` owns them.

Output:

```
Research phase open for <name>.
Agenda: initiatives/<name>/research/agenda.md
Explore freely in this conversation. Save progress with /spec-research-checkpoint, or conclude with /spec-research-end.
Tip: run /spec-research-checkpoint before /clear or compaction — it works from what is in context.
```
