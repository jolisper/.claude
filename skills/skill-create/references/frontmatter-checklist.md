# Skill Frontmatter Checklist

## Required fields

- `name`: kebab-case, 1–64 chars, no consecutive hyphens (`--`), no leading/trailing hyphens; matches the directory name
- `description`: imperative voice, user-intent focused, explicit trigger contexts, ≤1024 chars

## Claude Code fields — include when applicable

- `disable-model-invocation`: always include when targeting Claude Code
- `argument-hint`: include when the skill accepts a parameter; shown as UI placeholder
- `allowed-tools`: space-delimited; use Claude Code tool syntax (`Bash(git:*)`, `Read`, `Edit`, etc.) when targeting Claude Code
  - If scripts planned: include `Bash(bash:*)` in `allowed-tools`
- `when_to_use`: include to enable auto-discovery and skill-search routing
- `model`: include when the skill should run on a specific model (`haiku` for read-only/lookup skills; omit to inherit the session model)
- `effort`: include when reasoning depth matters (`low`/`medium`/`high`/`max`; `high` for analysis or drafting skills)
- `context`: `inline` (default) for interactive skills with confirmation gates; `fork` for isolated, non-interactive runs
- `paths`: ⚠ Do not use — skills with `paths` do not appear in the slash command list (confirmed broken in Claude Code)
- `skills`: include comma-separated skill names to preload when the skill orchestrates other skills
- `hooks`: include session-scoped lifecycle hooks when pre-flight validation or post-action verification adds value

## Optional base fields

Include only when genuinely relevant: `license`, `metadata`, `compatibility`
