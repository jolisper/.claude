---
name: try
description: Investigate and experiment with how to accomplish something in the current project. Launches the try agent in an isolated worktree with sandboxed external dependencies.
disable-model-invocation: true
argument-hint: "<what you want to try or investigate>"
allowed-tools: Agent
---

If `$ARGUMENTS` is empty, ask the user: "What would you like to try or investigate?"

Do not use in a directory that is not a git repository — the isolated worktree requires git.

## Agent contract

The `try` agent creates an isolated git worktree with sandboxed external dependencies, investigates the request, and pauses before irreversible steps. Its tool surface: `Bash(*)`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `AskUserQuestion`.

## Launch

Launch the `try` agent with the following request: `$ARGUMENTS`

## On completion

Relay the agent's structured summary to the user in this format:

```
What was tried: <description of what the agent explored>
Outcome: success / partial / blocked
Reproducible steps: <numbered steps, or "none found">
Risk warnings: <risks or caveats the agent surfaced, or "none">
```

## On failure

If the agent returns an error or cannot complete, report the error to the user verbatim. Common causes:
- **Not a git repo** — worktree creation requires git; suggest running from a git repository root.
- **Request too vague** — ask the user to be more specific about what to try.
