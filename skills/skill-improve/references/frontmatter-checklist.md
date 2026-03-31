# Skill Frontmatter Checklist

Check against `references/spec.md` for authoritative field definitions.

## HIGH findings (spec violations)

- `name` missing, not kebab-case, longer than 64 chars, contains consecutive hyphens (`--`), or doesn't match the directory name
- `description` missing
- `disable-model-invocation` absent on a Claude Code skill — must be explicitly declared
- `allowed-tools` uses JSON array syntax (`["Read", ...]`) — spec requires space-delimited string (`Read Grep`)
- `allowed-tools` includes tools the body never uses (over-permission)

## MEDIUM findings (best-practice gaps)

- `context` is `inline` (default) for a heavy, non-interactive workflow that pollutes the user's context — consider `fork`
- Body orchestrates other skills but `skills` not declared — sub-skills won't be preloaded at invocation time

## LOW findings (minor improvements)

- `when_to_use` absent — reduces auto-discovery and skill-search routing
- `when_to_use` is a near-paraphrase of `description` — both should add unique value; `when_to_use` should describe trigger conditions, `description` should describe what the skill does
- `model` not set for a read-only or lookup skill — `haiku` would reduce cost without quality loss
- `effort` absent on a complex analysis or drafting skill — `high` signals reasoning depth to the runtime
- `paths` absent on a skill with a natural file-context trigger (e.g. `**/SKILL.md`)
- `argument-hint` absent when the skill accepts user input via `$ARGUMENTS`
- `hooks` absent on a destructive skill — a pre-flight or post-action hook would add structural value
- Fields present that add no value (unnecessary fields inflate the frontmatter)
