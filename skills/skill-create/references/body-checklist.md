# Skill Body Checklist

## Structure

- Stepwise procedures ("do X, then Y") not declarations ("the output should be Z")
- Match prescriptiveness to reversibility: be strict for destructive ops, flexible elsewhere
- Use `$ARGUMENTS` to reference the user-supplied parameter (Claude Code)

## Interaction patterns

- Include confirmation gates before destructive actions
- Avoid compound Bash expressions (`&&`, `||`, pipes) in skill steps — they trigger approval prompts and interrupt flow; use separate Bash calls instead
- Follow the menu standard: "How do you want to proceed?" prompts use a lettered `(a)/(b)/...` menu; binary yes/no is expressed as `(a) Proceed / (b) Cancel` — never bare yes/no; item selection from a numbered list may use numeric input; every lettered menu that can abort a workflow includes a Cancel option

## Content

- Provide defaults, not menus — pick one approach and note alternatives briefly
- Inline output templates only when format consistency matters
- Keep SKILL.md under 500 lines; use `references/` files for large reference material
- Add only what the agent lacks; omit what it already knows
- For discipline-enforcing rules, include counter-rationalizations ("even when X, still do Y")
- Specify failure paths: error output format, recovery steps, subprocess failure contracts
- Include an explicit "when NOT to use / when to abort" section for destructive or context-sensitive skills
- When delegating to another skill or subprocess, explicitly restate tool restrictions and behavioral contracts at the boundary
- If logic overlaps with an existing sibling skill, reuse the same implementation pattern

## Scripts

- If scripts planned: use the path form that matches the **installation scope chosen in Phase 2**:
  - Global (`~/.claude/skills/`) → `~/.claude/skills/<name>/scripts/<script>.sh`
  - Project-local (`.claude/skills/`) → `$(pwd)/.claude/skills/<name>/scripts/<script>.sh`
  - (See `${CLAUDE_SKILL_DIR}/references/using-scripts.md` for the full rationale)
- If scripts planned: list available scripts in an `## Available scripts` section at the top of the body
