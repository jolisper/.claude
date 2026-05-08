---
name: skill-update
description: >
  Modify an existing skill with a new feature or behavior change. Reads the
  target skill, analyzes the proposed modification for contradictions or scope
  creep, asks clarifying questions when needed, and applies the change with your
  approval. May suggest creating a new skill instead when the modification would
  compromise the target skill's integrity.
disable-model-invocation: true
argument-hint: "<skill-name> <modification description>"
allowed-tools: Read Edit Write Glob Bash(mkdir:*)
when_to_use: >
  Invoke when the user wants to add a feature, change behavior, or extend an
  existing skill — e.g. "add X to skill-name", "update skill-name to also
  do Y", "modify skill-name so that Z".
effort: high
---

## Phase 1: Intake

Parse `$ARGUMENTS` as `<target> <modification>`:
- The first token (or quoted group) is the skill name or path.
- Everything after the first token is the modification description.

If `$ARGUMENTS` is empty: ask "Which skill do you want to update, and what should change?"

If the modification description is empty after extracting the target: ask "What modification do you want to make to `<name>`?"

Resolve the target skill file:
- If it looks like a file path (contains `/` or ends in `.md`): use it directly.
- If it looks like a skill name:
  - Try `~/.claude/skills/<name>/SKILL.md`.
  - If not found, try `.claude/skills/<name>/SKILL.md`.
  - If still not found, report and stop.

Read the resolved SKILL.md. If it cannot be read, report the error and stop.

**When NOT to proceed — stop and explain if:**
- The file has no YAML frontmatter block or no `name` field (not a valid skill)
- The skill is the one currently running this update (circular self-modification — offer to re-run after the session ends)

## Phase 2: Analyze

Read `~/.claude/skills/skill-create/references/spec.md`.
Read `~/.claude/skills/skill-create/references/best-practices.md`.

If either file cannot be read, report which failed and stop — do not proceed without the full spec.

With the skill content and modification description in hand, analyze three dimensions:

**A. Fit** — Does the modification align with the skill's stated purpose and `description` field?
- Flag if the modification clearly belongs to a different domain.
- Flag if it would make the skill do two unrelated things.

**B. Contradictions** — Does the modification conflict with existing instructions?
- Look for explicit rules the modification would violate (e.g. "never skip confirmations" + "add a --force flag").
- Look for logic the modification would duplicate redundantly.
- Look for workflow steps the modification would break or contradict.

**C. Scope** — Would the modification bloat the skill beyond its role?
- Estimate whether the modified skill would exceed 500 lines (tier 2 budget from spec).
- Consider whether the new behavior would be better as a standalone skill.

## Phase 3: Plan

Based on the analysis, determine the outcome and proceed with the first applicable case:

**Case 1 — Clean modification:** No contradictions, fits the skill's purpose, reasonable scope.
Draft the specific changes: list each section to add, edit, or remove. For frontmatter changes (new tools, changed fields), state them explicitly. For body changes, write the proposed new or edited text inline.

**Case 2 — Contradictions or incoherence:** The modification conflicts with existing instructions or is ambiguous.
Compose one batched clarification message covering all issues — never ask one at a time. Present each issue and offer options where applicable. Do not proceed to Phase 4 until all clarifications are resolved.

**Case 3 — Scope creep or domain mismatch:** The modification would compromise the skill's integrity.
Explain why it doesn't fit and offer one of:
- A reduced scope that fits within the skill, or
- Creating a new sibling skill instead: "This would work better as a new skill — run `/skill-create <description>` to build it."
Ask the user how they want to proceed before continuing.

## Phase 4: Review

Present the planned changes, then determine whether confirmation is needed:

**Trivial changes** (wording fix, adding one optional frontmatter field, single-sentence clarification): apply immediately without asking.

**Non-trivial changes** (new or restructured workflow steps, behavior changes, frontmatter additions that affect tool access or skill routing, new reference files): present the plan and ask:

```
Here are the proposed changes. How do you want to proceed?
(a) Apply as-is
(b) Adjust — tell me what to change
(c) Cancel
```

Wait for the user's response. On (b), revise the plan and ask again. Repeat until (a) or (c).

## Phase 5: Apply

Apply the approved changes using Edit to modify the existing SKILL.md in place.

If new reference files are needed: run `mkdir -p <skill-directory>/references` then Write each file.

**Post-apply verification:**
Re-read the edited SKILL.md. For each applied change, spot-check that the change is present. If any change cannot be verified, warn:

```
[WARN] Change "<description>" could not be verified — inspect manually.
```

After all edits, confirm:
```
Updated <path>/SKILL.md — <description of what changed>.
```

If any Edit or Write call fails: report which change failed, list what was already written to disk, and stop. Instruct the user to use `/rewind` to restore the file to its pre-edit state.
