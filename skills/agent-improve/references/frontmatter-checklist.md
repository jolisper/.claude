# Agent Frontmatter Checklist

Check against `references/spec.md` for authoritative field definitions.

## HIGH findings (spec violations — wrong types, format errors, undocumented fields, runtime failures)

- `name` missing or not kebab-case
- `description` missing
- `tools` uses JSON array syntax (`["Read", ...]`) — spec requires comma-separated string (`Read, Grep`)
- `model` set to an invalid value (not `sonnet`, `opus`, `haiku`, a full model ID, or `inherit`)
- `permissionMode` set to an invalid value (not `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan`)
- `memory` set to an invalid value (not `user`, `project`, `local`)
- Any field present that is not in the official spec (e.g. `color` — UI-only, not a file field)
- `AskUserQuestion` appears in body but is not listed in `tools` — tool call will fail at runtime

## MEDIUM findings (best-practice gaps that reduce reliability or clarity)

- `tools` includes `Bash` without restriction and no bash command appears in body instructions
- `tools` includes `WebFetch` and no fetch instruction appears in body
- `tools` lists any tool with no corresponding instruction in the body (overly broad grant)
- Agent is purely read-only/analysis but `permissionMode: plan` is not set
- `description` doesn't start with an imperative verb

## LOW findings (minor improvements)

- `model` not specified for a read-only or low-reasoning agent — `haiku` would reduce cost without quality loss
- `description` trigger contexts are vague
- `hooks` absent on an agent that performs destructive actions — a `Stop` hook running a verification pass would catch regressions automatically
- `permissionMode` not set to `plan` for a purely read-only/analysis agent
- `when_to_use` is a near-paraphrase of `description` — both fields should add unique value; `when_to_use` should describe trigger conditions, `description` should describe what the agent does