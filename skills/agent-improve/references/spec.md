# Anthropic Sub-Agents Frontmatter Spec

Source: https://code.claude.com/docs/en/sub-agents.md

## Storage locations

- **Global agents:** `~/.claude/agents/<name>.md` — available in all projects
- **Project agents:** `.claude/agents/<name>.md` — available only in that project
- Project agents take precedence over global agents with the same name.

## Frontmatter fields

All fields are optional unless marked **required**.

| Field | Type | Required | Valid values / notes |
|---|---|---|---|
| `name` | string | **required** | Kebab-case identifier. Used to invoke the agent. |
| `description` | string | **required** | Plain-text description. Claude Code uses this to decide when to invoke the agent automatically. Start with an imperative verb. ≤1024 chars recommended. |
| `tools` | string | optional | Comma-separated list of tool names the agent may call. Examples: `Read, Grep, Bash`. JSON array syntax (`["Read"]`) is **not** valid. Omit to allow all tools. |
| `disallowedTools` | string | optional | Comma-separated list of tools the agent must never call. |
| `model` | string | optional | Which Claude model to use. Valid values: `sonnet`, `opus`, `haiku`, a full model ID (e.g. `claude-opus-4-6`), or `inherit` (default — uses whatever the parent session uses). Any other value is invalid. |
| `permissionMode` | string | optional | Controls how the agent handles tool permissions. Valid values: `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`. Any other value is invalid. |
| `maxTurns` | integer | optional | Maximum number of agentic turns before the agent stops. Must be a positive integer. |
| `skills` | list | optional | Skills available to the agent. |
| `mcpServers` | list | optional | MCP servers available to the agent. |
| `hooks` | list | optional | Lifecycle hooks. |
| `memory` | string | optional | Memory scope. Valid values: `user`, `project`, `local`. Any other value is invalid. |
| `background` | boolean | optional | If `true`, the agent runs as a background task. |
| `isolation` | string | optional | Isolation mode for the agent's execution environment. |

## Fields that are NOT in the spec

The following fields have **no effect** when placed in an agent `.md` file. Do not add them:

- `color` — this is a UI-only setting in Claude Code's interface; it cannot be set via the agent file.
- `disable-model-invocation` — this is a **skill** frontmatter field, not an agent field.
- `argument-hint` — this is a **skill** frontmatter field, not an agent field.
- `allowed-tools` — this is a **skill** frontmatter field. The agent equivalent is `tools`.

## Tools field format

The `tools` value must be a **comma-separated string**, not a YAML list or JSON array:

```yaml
# correct
tools: Read, Grep, Bash

# wrong — YAML list syntax
tools:
  - Read
  - Grep

# wrong — JSON array syntax
tools: ["Read", "Grep"]
```

Tool restriction syntax (Bash only):
```yaml
tools: Read, Bash(git:*)
```

## AskUserQuestion

`AskUserQuestion` is a special tool that lets the agent pause and ask the user a clarifying question. If the agent body uses `AskUserQuestion`, it **must** be listed in `tools`, or the tool call will fail at runtime:

```yaml
tools: Read, Grep, AskUserQuestion
```

## Required vs inferred name

The `name` field must be kebab-case and should match the filename (without `.md`). Example: a file at `~/.claude/agents/code-reviewer.md` should have `name: code-reviewer`.
