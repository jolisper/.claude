# Agent System-Prompt Best Practices

## Write procedures, not persona descriptions

The system prompt is a set of instructions, not a character sheet. Every section should tell the agent *what to do*, not *what kind of entity it is*.

**Bad** (declarative):
> You are a thorough code reviewer who values correctness and clarity.

**Good** (procedural):
> 1. Read the diff with the Read tool.
> 2. For each changed function, check: does it handle the error cases? Are variable names clear?
> 3. Output findings grouped by file, ordered HIGH → MEDIUM → LOW.

## Define an intake protocol

Before reasoning, the agent must establish ground truth. Include an explicit first step that reads the relevant files, checks git state, or queries whatever context the agent needs.

**Why:** Agents that skip discovery reason about stale assumptions. An intake protocol makes the agent's starting state deterministic.

**Pattern:**
```
## Step 1: Gather context
Read <file>. Run <command>. If <condition> is not met, ask the user before continuing.
```

## Define escalation conditions

Specify exactly when the agent should stop and ask the user instead of proceeding.

**Why:** Without escalation conditions, agents either over-ask (annoying) or silently make wrong decisions (dangerous).

**Pattern:**
```
Stop and ask the user if:
- The target file does not exist.
- More than N files would be modified.
- The requested change conflicts with <constraint>.
```

To ask the user, use `AskUserQuestion`. This tool must be listed in `tools` in the frontmatter or it will fail at runtime.

## Specify output format

When the agent produces structured output (reports, diffs, summaries), define the exact format in the system prompt. Unspecified formats vary across invocations.

**Pattern:**
```
Output format:
[SEVERITY] <area> — <title>
           Problem: <fact>
           Fix: <action>
```

## Grant only the tools the body uses

Every tool in `tools` is a capability the agent can exercise — and a surface for mistakes. List only the tools that have a corresponding instruction in the body.

**Checklist:**
- `Bash` is listed → at least one bash command is instructed in the body
- `WebFetch` is listed → at least one fetch instruction exists
- `Edit` or `Write` is listed → the agent has explicit instructions for when and what to edit
- `AskUserQuestion` is listed → the body says when to use it

## Keep the system prompt lean

The system prompt is loaded on every invocation. Inline reference material (long specs, example outputs, static tables) inflates every call and makes the prompt harder to maintain.

**Rule:** Reference material belongs in `references/` files. The body reads them with the Read tool when needed.

**Signs of inline bloat:**
- Verbatim quotations from external specs
- Large static tables or enumerations
- Example outputs longer than ~10 lines
- Any block that starts "For reference, here is…"

## Read before writing

If the agent edits files, it must read them first. Editing without reading produces diffs against stale content.

**Pattern:**
```
Read <file> with the Read tool before making any edits.
```

## Prefer Edit over Write for existing files

`Write` overwrites the entire file. `Edit` makes targeted replacements. Use `Edit` for all modifications to existing files; reserve `Write` for creating new files.

## Confirmation gates for destructive actions

Any action that deletes, overwrites, or pushes data should have an explicit confirmation step:

```
Before applying fixes, ask:
"Apply N fix(es) to <file>? (yes / no)"
Wait for explicit approval.
```

## AskUserQuestion vs free-form output

Use `AskUserQuestion` (the tool) when you need structured user input mid-task. Use plain text output for reporting results. Do not use `AskUserQuestion` for announcements or status updates — that tool expects a response.
