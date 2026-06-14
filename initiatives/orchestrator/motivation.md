# Initiative: spec orchestrator skill

## Summary

A new `spec` orchestrator skill that generates both a functional and a technical spec
from a single invocation, keeping the main agent context clean by delegating all
reasoning to isolated sub-agents.

## Origin

The `spec-functional` and `spec-technical` skills already work well independently,
but require two manual invocations and fill the main context with intermediate
reasoning. A thin orchestrator can wire them together, fully automated, with no
main-context pollution.

## Design

### Invocation

```
/spec <hint or path to .md file>
```

### Execution flow

```
1. Read agents/functional.md and agents/technical.md into main context
2. Spawn Agent(A): prompt = functional.md contents + input  →  writes FUNCTIONAL.md
3. Spawn Agent(B): prompt = technical.md contents          →  reads FUNCTIONAL.md, writes TECHNICAL.md
```

Steps 2 and 3 are sequential — Agent(B) depends on the output of Agent(A).

### Context isolation

- Main context holds: parsed input, two agent prompt files (cheap reads), two spawn calls.
- All reading, reasoning, and drafting happens inside the sub-agents.
- Sub-agents receive self-contained prompts — no hidden file dependencies.

### File structure

```
~/.claude/
  skills/spec/
    SKILL.md              ← orchestrator (thin, wiring only)
  agents/
    spec/
      functional.md       ← full instructions for Agent(A)
      technical.md        ← full instructions for Agent(B)
```

Agent files live in `~/.claude/agents/spec/` following the official Claude Code
convention. User-scope agents (`~/.claude/agents/`) are available across all
projects. Subfolders are supported for organization; identity comes from the
`name` frontmatter field, not the path.

### Agent prompt design

The orchestrator reads each agent file in the main context and passes the contents
as the sub-agent prompt. Agent files are self-contained: they define inputs, steps,
outputs, and failure conditions without depending on any external files.

This is the same pattern as `scripts/` in other skills — reusable logic extracted
into dedicated files the skill delegates to, rather than duplicated inline.

### Fully automated

No checkpoints between steps. The orchestrator runs end-to-end without user input.
If Agent(A) fails to write FUNCTIONAL.md, Agent(B) will stop naturally (its
instructions require FUNCTIONAL.md to exist as input).

## Files

- `skills/spec/SKILL.md` — orchestrator skill
- `agents/spec/functional.md` — functional spec sub-agent instructions
- `agents/spec/technical.md` — technical spec sub-agent instructions

## Design principles

- Orchestrator stays thin: no spec logic, only wiring.
- Sub-agents are fully self-contained: prompts embed all instructions directly.
- Agent logic lives in dedicated files, not inline in the orchestrator.
- Main context accumulates nothing beyond two file reads and the spawn calls.
- Sequential by necessity: technical spec requires functional spec as input.

## Status

- [x] Initiative documented
- [ ] `agents/spec/functional.md` written
- [ ] `agents/spec/technical.md` written
- [ ] `skills/spec/SKILL.md` written
- [ ] Validated against a real feature description
