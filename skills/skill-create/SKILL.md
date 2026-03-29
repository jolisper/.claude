---
name: skill-create
description: >
  Use this skill when you want to create a new agent skill, slash command, or
  reusable agent capability — even with just a rough idea, a file to extract
  from, or a URL to base it on. Handles the full creation workflow: clarifying
  requirements, drafting a SKILL.md following the agentskills.io specification
  and best practices, and writing the file to disk. Applies agent-specific
  conventions for Claude Code, OpenCode, Gemini CLI, and Codex. Use even if
  you haven't decided on the skill name, target agent, or exact scope yet.
disable-model-invocation: false
argument-hint: "short description or URL/file reference for the skill to create"
allowed-tools: Write Read WebFetch Bash(mkdir:*)
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
6. **Installation scope** — global (`~/.claude/skills/`), project-local (`.claude/skills/`), or cross-client (`~/.agents/skills/` / `.agents/skills/`)? *(read `~/.claude/skills/skill-create/references/agent-conventions.md` for path details)*

Never ask about things that can be confidently inferred from the description or context.

## Phase 3: Draft

Before drafting frontmatter, read `~/.claude/skills/skill-create/references/spec.md`.
Before drafting the body, read `~/.claude/skills/skill-create/references/best-practices.md`.
If the target agent is not Claude Code, also read `~/.claude/skills/skill-create/references/agent-conventions.md`.

If any reference file cannot be read, report which file failed and stop — do not draft without the full spec and best-practices.

Even if the spec and best-practices feel familiar from a previous invocation, still read both reference files before drafting — the body checklist depends on their current content, which may have changed.

**Script evaluation:**
Before drafting, decide whether the skill would benefit from a bundled script.
Read `~/.claude/skills/skill-create/references/using-scripts.md` if any of these apply:
- Commands include complex flag values, format strings, or special characters
- The workflow chains multiple commands or involves a loop
- Text processing with patterns derived from user input
- Consistent behavior is critical and agent-constructed commands risk variation

If scripts are warranted, plan the script file(s) now and note them before the draft.

Produce a complete SKILL.md draft in a fenced code block.

**Frontmatter checklist:**
- `name`: kebab-case, 1–64 chars, no consecutive hyphens, matches the directory name
- `description`: imperative voice, user-intent focused, explicit trigger contexts, ≤1024 chars
- `disable-model-invocation`: always include when targeting Claude Code
- `argument-hint`: include when the skill accepts a parameter; shown as UI placeholder
- `allowed-tools`: space-delimited; use Claude Code tool syntax (`Bash(git:*)`, `Read`, `Edit`, etc.) when targeting Claude Code
- If scripts planned: include `Bash(bash:*)` in `allowed-tools`
- Include `license`, `metadata`, or `compatibility` only when genuinely relevant

**Body checklist (from best-practices):**
- Stepwise procedures ("do X, then Y") not declarations ("the output should be Z")
- Match prescriptiveness to reversibility: be strict for destructive ops, flexible elsewhere
- Use `$ARGUMENTS` to reference the user-supplied parameter (Claude Code)
- Include confirmation gates before destructive actions
- Follow the menu standard: "How do you want to proceed?" prompts use a lettered `(a)/(b)/...` menu; binary yes/no is expressed as `(a) Proceed / (b) Cancel` — never bare yes/no; item selection from a numbered list may use numeric input; every lettered menu that can abort a workflow includes a Cancel option
- Provide defaults, not menus — pick one approach and note alternatives briefly
- Inline output templates only when format consistency matters
- Keep SKILL.md under 500 lines; use `references/` files for large reference material
- Add only what the agent lacks; omit what it already knows
- For discipline-enforcing rules, include counter-rationalizations ("even when X, still do Y")
- Specify failure paths: error output format, recovery steps, subprocess failure contracts
- Include an explicit "when NOT to use / when to abort" section for destructive or context-sensitive skills
- When delegating to another skill or subprocess, explicitly restate tool restrictions and behavioral contracts at the boundary
- If logic overlaps with an existing sibling skill, reuse the same implementation pattern
- If scripts planned: use the path form that matches the **installation scope already chosen in Phase 2**:
  - Global (`~/.claude/skills/`) → `~/.claude/skills/<name>/scripts/<script>.sh`
  - Project-local (`.claude/skills/`) → `$(pwd)/.claude/skills/<name>/scripts/<script>.sh`
  - (See `~/.claude/skills/skill-create/references/using-scripts.md` for the full rationale)
- If scripts planned: list available scripts in an `## Available scripts` section at the top of the body

**If the skill needs reference files**, plan them out and note them at the bottom of the draft.

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
2. Attempt to Read `<skill-directory>/SKILL.md`. If it exists, ask:
   ```
   A skill named `<name>` already exists at `<path>`. How do you want to proceed?
   (a) Overwrite it
   (b) Cancel
   ```
   On (b): stop.
3. Run `mkdir -p <skill-directory>` and, if reference files were planned, `mkdir -p <skill-directory>/references`.
4. Write `SKILL.md` to `<skill-directory>/SKILL.md`.
4a. If scripts were planned: run `mkdir -p <skill-directory>/scripts` and write each script to `<skill-directory>/scripts/<name>.sh`.
5. Write any planned reference files to `<skill-directory>/references/`.
6. Confirm: "Skill created at `<path>/SKILL.md`."
