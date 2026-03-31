# agentskills.io — Frontmatter Specification

Source: https://agentskills.io/docs/specification
Fetch that URL for full details when in doubt.

## File layout

```
<skill-name>/
├── SKILL.md          # required — frontmatter + body
└── references/       # optional — large reference material
    └── *.md
```

The directory name must match the `name` field exactly.

## Frontmatter fields

All fields are optional except `name` and `description`.

| Field | Type | Rules |
|---|---|---|
| `name` | string | kebab-case; 1–64 chars; no consecutive hyphens (`--`); no leading/trailing hyphens; matches directory name |
| `description` | string | ≤1024 chars; imperative voice; user-intent focused; include explicit trigger contexts |
| `version` | string | semver (`1.0.0`) |
| `license` | string | SPDX identifier (e.g. `MIT`) |
| `metadata` | map | arbitrary key/value pairs for tooling |
| `compatibility` | list | agent identifiers this skill targets (e.g. `[claude-code, opencode]`) |
| `allowed-tools` | string | space-delimited tool names; agent-specific syntax applies |

## Claude Code-specific fields

These fields are supported by Claude Code but are not part of the base agentskills.io spec.

| Field | Type | Rules |
|---|---|---|
| `disable-model-invocation` | boolean | `true` = only user can invoke via `/name`; `false` = model may also auto-invoke |
| `argument-hint` | string | Shown as typeahead placeholder in CLI/IDE when typing `/skill-name` |
| `user-invocable` | boolean | Whether the skill is callable via `/name` |
| `when_to_use` | string | Trigger conditions for auto-invocation and skill-search discovery; improves routing |
| `model` | enum | `sonnet` / `opus` / `haiku` / `inherit` — override the session model for this skill |
| `effort` | enum | `low` / `medium` / `high` / `max` — override thinking depth |
| `context` | enum | `inline` (default — shares conversation context) or `fork` (isolated sub-agent) |
| `paths` | list | Glob patterns; skill auto-surfaces when working context matches (e.g. `["**/SKILL.md"]`) |
| `skills` | string | Comma-separated skill names preloaded when this skill activates |
| `hooks` | object | Session-scoped lifecycle hooks (active only while this skill runs, then cleaned up) |

## Description best practices

- Start with an imperative verb: "Use this skill when…", "Run this skill to…"
- State explicit trigger contexts — when should the agent invoke it?
- Mention what the skill does, not how it works
- Keep it scannable: no run-on sentences

## Body format

Plain markdown. No required structure — use headings, lists, or prose as appropriate.

The body is the skill's prompt. It runs as the instruction set given to the agent when the skill is invoked.
