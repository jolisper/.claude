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

## Description best practices

- Start with an imperative verb: "Use this skill when…", "Run this skill to…"
- State explicit trigger contexts — when should the agent invoke it?
- Mention what the skill does, not how it works
- Keep it scannable: no run-on sentences

## Body format

Plain markdown. No required structure — use headings, lists, or prose as appropriate.

The body is the skill's prompt. It runs as the instruction set given to the agent when the skill is invoked.
