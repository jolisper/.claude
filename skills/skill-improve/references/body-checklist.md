# Skill Body Checklist

Check against `references/best-practices.md` for detailed guidance on each item.

## HIGH findings (spec violations or runtime failures)

- A tool is used in the body but missing from `allowed-tools` (runtime failure)

## MEDIUM findings (best-practice gaps)

- Instructions are declarative ("output should be Z") not stepwise procedures ("do X, then Y")
- Destructive or irreversible actions lack explicit confirmation gates
- Menu standard violated: lettered menus missing a Cancel option, or bare yes/no used instead of `(a) Proceed / (b) Cancel`; every `(a)/(b)/...` menu that can abort a workflow must include a Cancel option
- `$ARGUMENTS` not checked at the start — skill doesn't ask for input when `$ARGUMENTS` is empty
- Compound Bash expressions (`&&`, `||`, pipes) used in skill steps — they trigger approval prompts and interrupt flow; prefer separate Bash calls
- Failure paths not specified: missing error output format, recovery steps, or subprocess failure contracts
- "When NOT to use / abort" section absent for destructive or context-sensitive skills
- Delegation boundaries don't restate tool restrictions and behavioral contracts when handing off to sub-skills
- Shared logic with sibling skills uses a different implementation (silent divergence risk)

## LOW findings (minor improvements)

- Large reference material embedded inline instead of in `references/` files
- SKILL.md exceeds 500 lines
- Documenting what the agent already knows (adds weight without value)
- Discipline-enforcing rules lack counter-rationalizations for likely skip scenarios (e.g. "even when X, still do Y")
