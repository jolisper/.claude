# Backup Enforcement Before Risky Operations

## Goal

Before Claude runs any risky command or procedure that could cause information/code loss, automatically create a rollback point.

## Implementation options

### Option A: Global `CLAUDE.md` instruction (soft enforcement)

Add a rule to `~/.claude/CLAUDE.md` telling Claude to always run a backup step before destructive operations.

- **Pros:** Zero configuration, works everywhere
- **Cons:** Not system-enforced — relies on Claude following the instruction. No guarantee it runs.

### Option B: `PreToolUse` hook in `settings.json` (hard enforcement)

Configure a hook that fires before every tool call. The hook script inspects the command and, if it matches a risky pattern (e.g. `git reset`, `git rebase`, `git checkout --`, `rm -rf`), runs a backup before proceeding.

- **Pros:** System-enforced regardless of what Claude does
- **Cons:** Needs a script to define risky patterns. Bash-only — won't intercept Edit/Write tool overwrites directly. Can be noisy.

### Option C: Both (recommended baseline)

CLAUDE.md instruction sets intent; hook acts as a safety net.

## Backup mechanism options

| Mechanism | Command | When it fits |
|---|---|---|
| `git stash push` | `git stash push -m "claude-rollback-$(date +%s)"` | Git repos, before rebases/resets; clean, temporary |
| Checkpoint commit | `git add -A && git commit -m "claude-checkpoint: ..."` | Git repos; permanent but pollutes history |
| File copy | `cp -r . ../backup-$(date +%s)` | Non-git dirs or files outside the repo |

## Recommended approach

**Option B (`PreToolUse` hook) + `git stash` as the backup mechanism**, scoped to git repos.

The hook intercepts risky Bash commands matching patterns like `git reset`, `git rebase`, `git checkout --`, `rm -rf`, etc., and runs `git stash push -m "claude-rollback-$(date +%s)"` before the command executes.

## Open questions (to resolve before implementing)

1. Should this cover only git repos, or also arbitrary directories?
2. Should the Edit/Write tools (file overwrites) also be covered, or just Bash commands?
3. `git stash` (clean, temporary) or checkpoint commit (permanent, visible in history)?
