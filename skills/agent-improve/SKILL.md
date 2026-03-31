---
name: agent-improve
description: >
  Use this skill to audit and improve an existing Claude Code agent. Invoke when
  you want to analyze an agent's .md file against the Anthropic sub-agents spec
  and best practices, see a prioritized list of issues, and apply fixes with your
  approval. Accepts an agent name (e.g. "architect") or a direct path to an
  agent .md file.
disable-model-invocation: true
argument-hint: "agent name or path to agent .md file"
allowed-tools: Read Edit Glob
when_to_use: >
  Invoke when the user wants to audit, improve, or fix an existing agent.
effort: high
paths:
  - ".claude/agents/**/*.md"
  - "agents/**/*.md"
---

## Phase 1: Locate the agent

Read `$ARGUMENTS`.

- If empty: ask "Which agent would you like to improve? Give me an agent name or path to an agent .md file."
- If it looks like a file path (contains `/` or ends in `.md`): use it directly.
- If it looks like an agent name (no `/`, no extension):
  - Try `~/.claude/agents/<name>.md` first.
  - If not found, try `.claude/agents/<name>.md`.
  - If still not found, ask the user to provide the full path.

Read the resolved agent .md file. If it cannot be read, report the error and stop.

## Phase 2: Analyze

Read `${CLAUDE_SKILL_DIR}/references/spec.md`.
Read `${CLAUDE_SKILL_DIR}/references/best-practices.md`.

Analyze the agent file against both documents. Check frontmatter and body separately.

**Frontmatter** (against `references/spec.md`):

HIGH findings (spec violations — wrong types, format errors, undocumented fields, runtime failures):
- `name` missing or not kebab-case
- `description` missing
- `tools` uses JSON array syntax (`["Read", ...]`) — spec requires comma-separated string (`Read, Grep`)
- `model` set to an invalid value (not `sonnet`, `opus`, `haiku`, a full model ID, or `inherit`)
- `permissionMode` set to an invalid value (not `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`)
- `memory` set to an invalid value (not `user`, `project`, `local`)
- Any field present that is not in the official spec (e.g. `color` — UI-only, not a file field)
- `AskUserQuestion` appears in body but is not listed in `tools` — tool call will fail at runtime

MEDIUM findings (best-practice gaps that reduce reliability or clarity):
- `tools` includes `Bash` without restriction and no bash command appears in body instructions
- `tools` includes `WebFetch` and no fetch instruction appears in body
- `tools` lists any tool with no corresponding instruction in the body (overly broad grant)
- Agent is purely read-only/analysis but `permissionMode: plan` is not set
- `description` doesn't start with an imperative verb

LOW findings (minor improvements):
- `model` not specified for a read-only or low-reasoning agent — `haiku` would reduce cost without quality loss
- `description` trigger contexts are vague
- `hooks` absent on an agent that performs destructive actions — a `Stop` hook running a verification pass would catch regressions automatically
- `permissionMode` not set to `plan` for a purely read-only/analysis agent

**Body** (against `references/best-practices.md`):

HIGH findings:
- A tool is instructed in the body but missing from `tools` (runtime failure)

MEDIUM findings:
- Instructions are declarative ("the agent should…") not procedural ("run…, read…, then…")
- No intake/discovery section — agent reasons without first establishing the ground truth
- No escalation conditions defined (when should the agent stop and ask the user?)
- Body is a character description with no behavioral procedures
- Verbatim quotations or large static reference blocks embedded inline (always loaded, cannot be deferred)

LOW findings:
- Output format not specified (agent outputs vary across invocations)
- Body exceeds ~300 lines (heavy system prompt; review for deferrable content)
- Persona section is purely declarative and adds no behavioral guidance

## Phase 3: Report

Present findings using this format:

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

Wait for the user's response. On (d), ask which items to apply and confirm the selection before proceeding.

## Phase 5: Apply

> Note: if you want to undo these edits after applying, use `/rewind` to restore the conversation and file state to before this skill ran.

Apply only the approved fixes. Edit the agent .md file in place using the Edit tool.

After all edits, show a summary:

```
Updated <path> — <N> fix(es) applied.
```

List each fix applied in one line: `[SEVERITY] <title> — done`.
