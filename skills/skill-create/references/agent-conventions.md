# Agent-Specific Conventions

Source: https://agentskills.io/docs/agents
Fetch that URL for full details when in doubt.

## Universal cross-client paths

The `.agents/skills/` directory has emerged as the widely-adopted convention for cross-client skill sharing. Any compliant agent scans it, so skills installed there are automatically visible across clients without duplication:

| Scope | Path |
|---|---|
| Project-local | `<project>/.agents/skills/<skill-name>/` |
| User-global | `~/.agents/skills/<skill-name>/` |

Use `.agents/skills/` when the skill should be available to multiple agents without separate installs. Use the client-native path (`~/.claude/skills/`, etc.) when targeting a specific agent only.

## Claude Code

**Install paths:**
- Global: `~/.claude/skills/<skill-name>/SKILL.md`
- Project-local: `.claude/skills/<skill-name>/SKILL.md`

**Frontmatter extensions (Claude Code only):**

| Field | Type | Description |
|---|---|---|
| `disable-model-invocation` | bool | `true` = user-only; `false` = Claude can also invoke it |
| `argument-hint` | string | Placeholder shown in the UI when the user types `/<skill-name> ` |

**`allowed-tools` syntax:**
- Tool names: `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`, `WebFetch`, `WebSearch`, `Agent`, `Skill`
- Bash restrictions: `Bash(git:*)` allows all git subcommands; `Bash(npm run:*)` allows `npm run <anything>`; `Bash(*)` allows all
- Multiple tools: space-delimited — `Read Edit Bash(git:*)`

**`$ARGUMENTS`:** The text typed after the skill name in the UI. Empty string if none provided.

**Invocation:** `/skill-name [arguments]` in the Claude Code UI.

## OpenCode

**Install path:** `.opencode/skills/<skill-name>/SKILL.md` (project-local only, no global)

**Frontmatter:** Uses the base agentskills.io spec — no extensions. `allowed-tools` is respected.

**`$ARGUMENTS`:** Supported with the same `$ARGUMENTS` token.

**Invocation:** `/skill-name [arguments]`

## Gemini CLI

**Install path:** `~/.gemini/skills/<skill-name>/SKILL.md` (global) or `.gemini/skills/` (project)

**Frontmatter:** Base spec only. No `disable-model-invocation` or `argument-hint`.

**`$ARGUMENTS`:** Not supported — Gemini CLI does not pass arguments to skills.

**Invocation:** `/skill-name` (no arguments)

**Notes:** Keep bodies concise — Gemini CLI has a shorter effective context for skill prompts.

## Codex (OpenAI)

**Install path:** `~/.codex/skills/<skill-name>/SKILL.md` (global) or `.codex/skills/` (project)

**Frontmatter:** Base spec only. No Claude Code extensions.

**`$ARGUMENTS`:** Supported.

**`allowed-tools` values:** `read_file`, `write_file`, `run_command`, `web_search` — different from Claude Code syntax. Do not use Claude Code tool names for Codex-targeted skills.

**Invocation:** `/skill-name [arguments]`

## Universal skills (agentskills.io only)

Skills targeting multiple agents should:
1. Use only base agentskills.io frontmatter fields
2. Avoid agent-specific tool names in `allowed-tools`
3. Note the `compatibility` list to declare which agents are supported
4. Avoid `$ARGUMENTS` in the body, or guard with a fallback when it may not be supported

## Compatibility field

```yaml
compatibility:
  - claude-code
  - opencode
  - gemini-cli
  - codex
```

Use when the skill targets a specific subset of agents.
