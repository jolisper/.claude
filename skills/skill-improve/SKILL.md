---
name: skill-improve
description: >
  Audit and improve an existing skill. Reads the target SKILL.md, analyzes it
  against the agentskills.io specification and best practices, produces a
  prioritized list of HIGH/MEDIUM/LOW findings, and applies fixes with your
  approval. Accepts a skill name (e.g. "git-log") or a direct path to a SKILL.md
  file.
disable-model-invocation: true
argument-hint: "<skill name or path to SKILL.md> [focal point]"
allowed-tools: Read Edit Write Glob Bash(mkdir:*)
when_to_use: >
  Invoke when the user names a skill to review or improve, shares a SKILL.md
  path, or is editing a SKILL.md file. Also surfaces automatically when any
  SKILL.md is in the working context.
effort: high
paths:
  - "**/SKILL.md"
---

## Phase 1: Locate the skill

Parse `$ARGUMENTS` as two parts: `<target>` and an optional `<focal-point>`.

- The first token (or quoted group) is the target (skill name or file path).
- Everything after the first token is the focal point — a free-form string describing what aspect to focus on (e.g. "frontmatter", "script reliability", "argument handling"). May be empty.

If `$ARGUMENTS` is empty: ask "Which skill would you like to improve? Give me a skill name or path to a SKILL.md file."

Resolve the target:
- If it looks like a file path (contains `/` or ends in `.md`): use it directly.
- If it looks like a skill name (no `/`, no extension):
  - Try `~/.claude/skills/<name>/SKILL.md` first.
  - If not found, try `.claude/skills/<name>/SKILL.md`.
  - If still not found, ask the user to provide the full path.

Read the resolved SKILL.md. If it cannot be read, report the error and stop.

If the resolved path exists but is not inside a recognized `skills/` directory (i.e. neither `~/.claude/skills/` nor `.claude/skills/`), warn the user and ask:

```
This file is not inside a skills/ directory. Proceed anyway?
(a) Proceed
(b) Cancel
```

If a focal point was provided, note it — you will use it in Phase 2 and Phase 3.

**When NOT to proceed — stop and explain if any of these apply:**
- The resolved file is empty or contains no YAML frontmatter block
- The file has no `name` or `description` field (not a valid skill)
- The skill is the one currently running this audit (circular self-improvement — offer to re-run after the session)

## Phase 2: Analyze

Read `${CLAUDE_SKILL_DIR}/references/spec.md`.
Read `${CLAUDE_SKILL_DIR}/references/best-practices.md`.
Read `${CLAUDE_SKILL_DIR}/references/using-scripts.md`.
Read `${CLAUDE_SKILL_DIR}/references/frontmatter-checklist.md`.
Read `${CLAUDE_SKILL_DIR}/references/body-checklist.md`.

If any reference file cannot be read, report which file failed and stop — do not proceed with an incomplete checklist.

Analyze the skill against all five documents. Even if the skill looks well-written at a glance, complete every item in every checklist section — common issues hide in details like allowed-tools minimality, missing $ARGUMENTS gates, and absent failure paths. If a focal point was provided, give it extra scrutiny — look specifically for issues related to that area while still running the full checklist.

Check frontmatter against `references/frontmatter-checklist.md` and body against `references/body-checklist.md`.

**Script evaluation** (using criteria from `references/using-scripts.md`):
- Does the skill run commands with complex flag values, format strings, or special characters?
- Does it chain multiple commands with `&&`, `||`, or `echo "..."` separators? (flag as flow-interruption issue — prefer separate Bash calls; move to a script only if complexity warrants it)
- Does it involve loops, conditional branching, or batch iteration?
- Does it use text processing (`grep`, `awk`, `sed`) with patterns derived from user input?
- Is consistent, reproducible behavior critical — where agent-constructed commands risk variation?

If any apply and no scripts exist yet: flag as a finding that a `scripts/` file would improve reliability.

**Existing scripts audit:**
If the skill directory contains a `scripts/` folder, read each script file and evaluate against the best practices in `references/using-scripts.md`:
- No interactive prompts — all input via flags, env vars, or stdin
- `--help` flag implemented with documented flags and examples
- Errors include what was expected and what to try next (stderr, non-zero exit)
- Output uses structured format (`status=…` key=value or JSON on stdout); diagnostics to stderr
- Idempotent — safe to retry without side effects
- Output size is predictable; large output defaults to a summary with `--offset` support

Also verify the SKILL.md references scripts using the correct path form for the install scope (global → hardcoded `~/.claude/skills/…`; project-local → `$(pwd)/.claude/skills/…`) and that `Bash(bash:*)` is in `allowed-tools`.

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

- **HIGH** — spec violations (missing required fields, wrong types, format errors)
- **MEDIUM** — best-practice gaps that reduce reliability or clarity; script recommendations and script best-practice violations fall here
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

If the target skill directory is under version control and has unstaged changes, show the affected files and ask:

```
Unstaged changes exist in this skill directory. Proceed anyway?
(a) Proceed
(b) Cancel
```

Wait for the user's reply before applying any edits.

> Note: if you want to undo these edits after applying, use `/rewind` to restore the conversation and file state to before this skill ran.

Apply only the approved fixes. Edit the SKILL.md in place using the Edit tool. Edit existing scripts in place using the Edit tool.

If any Edit call fails (e.g. `old_string` not found), report which fix failed and stop — do not attempt remaining fixes. Instruct the user to use `/rewind` to restore the file to its pre-edit state.

If a script recommendation was approved: run `mkdir -p <skill-directory>/scripts`, write the script to `<skill-directory>/scripts/<name>.sh`, and update `allowed-tools` in the frontmatter to include `Bash(bash:*)`.

**Post-apply verification:**
Re-read the edited file. For each applied fix, spot-check that the change is present (search for a key string the fix introduced or confirm a removed string is gone). If any fix cannot be verified, append a warning to the summary:

```
[WARN] Fix "<title>" could not be verified in the re-read file — inspect manually.
```

After all edits, show a summary:

```
Updated <path>/SKILL.md — <N> fix(es) applied.
```

List each fix applied in one line: `[SEVERITY] <title> — done`.
