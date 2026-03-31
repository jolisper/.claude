---
name: agent-improve
description: >
  Audit and improve an existing Claude Code agent. Reads the agent's .md file,
  analyzes it against the Anthropic sub-agents spec and best practices, produces
  a prioritized list of HIGH/MEDIUM/LOW issues, and applies fixes with your
  approval. Accepts an agent name (e.g. "architect") or a direct path to an
  agent .md file.
disable-model-invocation: true
argument-hint: "agent name or path to agent .md file [focal point]"
allowed-tools: Read Edit
when_to_use: >
  Invoke when the user names an agent to review or improve, shares an agent .md
  file path, or asks why an agent isn't behaving correctly. Also surfaces
  automatically when editing files in .claude/agents/ or agents/.
effort: high
paths:
  - ".claude/agents/**/*.md"
  - "agents/**/*.md"
---

## Phase 1: Locate the agent

Parse `$ARGUMENTS` as two parts: `<target>` and an optional `<focal-point>`.

- The first token (or quoted group) is the target (agent name or file path).
- Everything after the first token is the focal point — a free-form string describing what aspect to focus on (e.g. "frontmatter", "escalation conditions", "tool grants"). May be empty.

If `$ARGUMENTS` is empty: ask "Which agent would you like to improve? Give me an agent name or path to an agent .md file."

Resolve the target:
- If it looks like a file path (contains `/` or ends in `.md`): use it directly.
- If it looks like an agent name (no `/`, no extension):
  - Try `~/.claude/agents/<name>.md` first.
  - If not found, try `.claude/agents/<name>.md`.
  - If still not found, ask the user to provide the full path.

Read the resolved agent .md file. If it cannot be read, report the error and stop.

If the resolved path exists but is not inside a recognized `agents/` directory (i.e. neither `~/.claude/agents/` nor `.claude/agents/`), warn the user and ask:

```
This file is not inside an agents/ directory. Proceed anyway?
(a) Proceed
(b) Cancel
```

If a focal point was provided, note it — you will use it in Phase 2 and Phase 3.

## Phase 2: Analyze

Read `${CLAUDE_SKILL_DIR}/references/spec.md`.
Read `${CLAUDE_SKILL_DIR}/references/best-practices.md`.
Read `${CLAUDE_SKILL_DIR}/references/frontmatter-checklist.md`.
Read `${CLAUDE_SKILL_DIR}/references/body-checklist.md`.

If any reference file cannot be read, report which file failed and stop — do not proceed with an incomplete checklist.

Analyze the agent file against all four documents. Even if the agent looks well-written at a glance, complete every item in both checklists — common issues hide in overly broad tool grants and missing escalation conditions. If a focal point was provided, give it extra scrutiny — look specifically for issues related to that area while still running the full checklist. Check frontmatter against `references/frontmatter-checklist.md` and body against `references/body-checklist.md`.

## Phase 3: Report

If a focal point was provided, open the report with a short paragraph (2–3 sentences) summarising what you found specifically in that area — even if the finding is "no issues in this area." Then present all findings using this format:

```
[HIGH]   <area> — <short title>
         Problem: <observable fact>
         Fix: <concrete change to make>

[MEDIUM] <area> — <short title>
         Problem: <observable fact>
         Fix: <concrete change to make>

[LOW]    <area> — <short title>
         Problem: <observable fact>
         Fix: <concrete change to make>
```

- **HIGH** — spec violations (missing required fields, wrong types, undocumented fields, runtime failures)
- **MEDIUM** — best-practice gaps that reduce reliability or clarity
- **LOW** — minor improvements (wording, optional fields, housekeeping)

If no issues are found, say so clearly and stop.

## Phase 4: Confirm

After the report, ask:

```
How do you want to proceed?
(a) Apply all fixes
(b) Apply HIGH and MEDIUM only
(c) Apply HIGH only
(d) Pick specific items — tell me which
(e) Cancel
```

Wait for the user's response. On (d), ask which items to apply. Show a summary of the selected fixes and ask:

```
Apply these N fix(es)?
(a) Proceed
(b) Cancel
```

Wait for confirmation before proceeding.

## Phase 5: Apply

If the target agent file is under version control and has unstaged changes, show the affected files and ask:

```
Unstaged changes exist in this agent file. Proceed anyway?
(a) Proceed
(b) Cancel
```

Wait for the user's reply before applying any edits.

> Note: if you want to undo these edits after applying, use `/rewind` to restore the conversation and file state to before this skill ran.

Apply only the approved fixes. Edit the agent .md file in place using the Edit tool.

If any Edit call fails (e.g. `old_string` not found), report which fix failed and stop — do not attempt remaining fixes. Instruct the user to use `/rewind` to restore the file to its pre-edit state.

**Post-apply verification:**
Re-read the edited file. For each applied fix, spot-check that the change is present (search for a key string the fix introduced or confirm a removed string is gone). If any fix cannot be verified, append a warning to the summary:

```
[WARN] Fix "<title>" could not be verified in the re-read file — inspect manually.
```

After all edits, show a summary:

```
Updated <path> — <N> fix(es) applied.
```

List each fix applied in one line: `[SEVERITY] <title> — done`.
