---
name: skill-create
description: >
  Create a new agent skill from scratch. Runs a full creation workflow: clarifies
  requirements, proposes a skill name, drafts a SKILL.md following the
  agentskills.io specification and best practices, self-audits the draft, and
  writes it to disk. Supports Claude Code, OpenCode, Gemini CLI, Codex, and
  universal cross-client skills.
disable-model-invocation: true
argument-hint: "short description or URL/file reference for the skill to create"
allowed-tools: Write Read WebFetch Bash(mkdir:*)
when_to_use: >
  Invoke when the user wants a new skill, slash command, or reusable capability
  — even with just a rough idea, an existing file to extract from, or a URL to
  base it on. Also use when the user wants to formalize a repeated workflow or
  extract a pattern into a reusable skill.
effort: high
---

## Phase 1: Intake

Read `$ARGUMENTS`.

- If empty, ask: "What skill would you like to create? Give me a description, file path, or URL."
- If `$ARGUMENTS` starts with `http://` or `https://`, fetch it with WebFetch and use the content as design context. If WebFetch returns an error, report the URL and error to the user and ask them to provide a plain description instead.
- If `$ARGUMENTS` looks like a file path (contains `/` or `\` or ends in a known extension), read it with Read and use the content as design context. If Read fails, report the path and error to the user and ask them to provide a plain description instead.
- Otherwise treat it as a plain description and proceed to Phase 2.

## Phase 2: Clarify (single batched message)

Ask all questions at once — never one at a time. Always ask:

1. **Target agent(s)** — Claude Code (default), OpenCode, Gemini CLI, Codex, or universal (agentskills.io only)?
2. **Skill name** — propose a kebab-case name derived from the description and ask the user to confirm or correct it.

Ask only when genuinely unclear from context:

3. **Scope** — if the description could mean multiple things, clarify intent.
4. **Confirmation gates** — does this skill perform destructive or irreversible actions (writes, deletes, pushes)?
5. **`disable-model-invocation`** — user-only (`true`, default) or also invokable by Claude (`false`)?
6. **Installation scope** — global (`~/.claude/skills/`), project-local (`.claude/skills/`), or cross-client (`~/.agents/skills/` / `.agents/skills/`)? *(read `${CLAUDE_SKILL_DIR}/references/agent-conventions.md` for path details)*

Never ask about things that can be confidently inferred from the description or context.

## Phase 3: Draft

Before drafting, read all reference files:
- `${CLAUDE_SKILL_DIR}/references/spec.md`
- `${CLAUDE_SKILL_DIR}/references/best-practices.md`
- `${CLAUDE_SKILL_DIR}/references/frontmatter-checklist.md`
- `${CLAUDE_SKILL_DIR}/references/body-checklist.md`

If the target agent is not Claude Code, also read `${CLAUDE_SKILL_DIR}/references/agent-conventions.md`.

If any reference file cannot be read, report which file failed and stop — do not draft without the full spec and best-practices.

Even if these feel familiar from a previous invocation, still read all reference files before drafting — the checklists depend on their current content, which may have changed.

**Script evaluation:**
Before drafting, decide whether the skill would benefit from a bundled script.
Read `${CLAUDE_SKILL_DIR}/references/using-scripts.md` if any of these apply:
- Commands include complex flag values, format strings, or special characters
- The workflow chains multiple commands or involves a loop
- Text processing with patterns derived from user input
- Consistent behavior is critical and agent-constructed commands risk variation

If scripts are warranted, plan the script file(s) now and note them before the draft.

Produce a complete SKILL.md draft in a fenced code block.

Apply the frontmatter checklist from `${CLAUDE_SKILL_DIR}/references/frontmatter-checklist.md`.

Apply the body checklist from `${CLAUDE_SKILL_DIR}/references/body-checklist.md`.

**If the skill needs reference files**, plan them out and note them at the bottom of the draft.

**Self-audit before presenting:**
Before moving to Phase 4, re-read the draft you just produced and verify it against `${CLAUDE_SKILL_DIR}/references/frontmatter-checklist.md` and `${CLAUDE_SKILL_DIR}/references/body-checklist.md`. If any checklist item is violated, fix the draft now — do not present a draft you know violates the checklist. This step is not optional even when the draft "looks good" — systematic verification catches issues that pattern-matching misses.

## Phase 4: Review

Present the draft, then ask:

```
Here's the draft. How do you want to proceed?
(a) Create it as-is
(b) Adjust — tell me what to change
(c) Cancel
```

Wait for the user's response. If (b), apply the requested changes, show the updated draft, and ask again. Repeat until (a) or (c).

## Phase 5: Write

On (a):

1. Determine the install path from Phase 2 (global or project-local) and the confirmed skill name.
2. Validate the confirmed skill name: it must be kebab-case, 1–64 chars, no consecutive hyphens (`--`), no leading/trailing hyphens. If invalid, warn the user and ask for a corrected name before proceeding.
3. Attempt to Read `<skill-directory>/SKILL.md`. If it exists, ask:
   ```
   A skill named `<name>` already exists at `<path>`. How do you want to proceed?
   (a) Overwrite it
   (b) Cancel
   ```
   On (b): stop.
4. Run `mkdir -p <skill-directory>` and, if reference files were planned, `mkdir -p <skill-directory>/references`.
5. Write `SKILL.md` to `<skill-directory>/SKILL.md`.
5a. If scripts were planned: run `mkdir -p <skill-directory>/scripts` and write each script to `<skill-directory>/scripts/<name>.sh`.
6. Write any planned reference files to `<skill-directory>/references/`.
7. Confirm: "Skill created at `<path>/SKILL.md`."

If any Write or Bash call in steps 4–6 fails, report which step failed, list what was already written to disk, and stop. Instruct the user to manually remove any partially written files before retrying.
