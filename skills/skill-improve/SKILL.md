---
name: skill-improve
description: >
  Use this skill to audit and improve an existing skill. Invoke when you want to
  analyze a skill's SKILL.md against the agentskills.io specification and best
  practices, see a prioritized list of issues, and apply fixes with your approval.
  Accepts a skill name (e.g. "git-log") or a direct path to a SKILL.md file.
disable-model-invocation: true
argument-hint: "<skill name or path to SKILL.md> [focal point]"
allowed-tools: Read Edit Write Glob Bash(mkdir:*)
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

If a focal point was provided, note it — you will use it in Phase 2 and Phase 3.

## Phase 2: Analyze

Read `~/.claude/skills/skill-improve/references/spec.md`.
Read `~/.claude/skills/skill-improve/references/best-practices.md`.
Read `~/.claude/skills/skill-improve/references/using-scripts.md`.

If any reference file cannot be read, report which file failed and stop — do not proceed with an incomplete checklist.

Analyze the skill against all three documents. Even if the skill looks well-written at a glance, complete every item in every checklist section — common issues hide in details like allowed-tools minimality, missing $ARGUMENTS gates, and absent failure paths. If a focal point was provided, give it extra scrutiny — look specifically for issues related to that area while still running the full checklist. Check:

**Frontmatter:**
- `name` is present, kebab-case, 1–64 chars, no consecutive hyphens, matches the directory name
- `description` is present, starts with an imperative verb, ≤1024 chars, includes trigger contexts
- `disable-model-invocation` is present (Claude Code target)
- `argument-hint` is present when the skill accepts user input via `$ARGUMENTS`
- `allowed-tools` is minimal — no tools granted that the body never uses; uses Claude Code syntax
- No fields present that aren't needed

**Body:**
- Instructions are stepwise procedures ("do X, then Y"), not declarations ("output should be Z")
- Destructive or irreversible actions have explicit confirmation gates
- Menu standard: "How do you want to proceed?" prompts use a lettered `(a)/(b)/...` menu; binary yes/no is expressed as `(a) Proceed / (b) Cancel` — never bare yes/no; item selection from a numbered list may use numeric input; every lettered menu that can abort a workflow includes a Cancel option
- `$ARGUMENTS` is checked at the start; skill asks for input if empty
- Large reference material lives in `references/` files, not inline
- SKILL.md is under 500 lines
- No documenting what the agent already knows
- Discipline-enforcing rules include counter-rationalizations for likely skip scenarios
- Failure paths are specified: error output format, recovery steps, subprocess failure contracts
- Explicit "when NOT to use / abort" conditions are present for destructive or context-sensitive skills
- Delegation boundaries explicitly restate tool restrictions and behavioral contracts
- Shared logic with sibling skills uses the same implementation (no silent divergence)

**Script evaluation** (using criteria from `references/using-scripts.md`):
- Does the skill run commands with complex flag values, format strings, or special characters?
- Does it chain multiple commands with `&&`, `||`, or `echo "..."` separators?
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

Wait for the user's response. On (d), ask which items to apply and confirm the selection before proceeding.

## Phase 5: Apply

If the target skill directory is under version control and has unstaged changes, note this to the user before applying — so they can commit or stash first if they want a clean diff.

Apply only the approved fixes. Edit the SKILL.md in place using the Edit tool. Edit existing scripts in place using the Edit tool.

If a script recommendation was approved: run `mkdir -p <skill-directory>/scripts`, write the script to `<skill-directory>/scripts/<name>.sh`, and update `allowed-tools` in the frontmatter to include `Bash(bash:*)`.

After all edits, show a summary:

```
Updated <path>/SKILL.md — <N> fix(es) applied.
```

List each fix applied in one line: `[SEVERITY] <title> — done`.
