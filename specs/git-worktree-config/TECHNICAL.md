# git-worktree-config — Technical Plan

## Context

The `git-worktree` skill's `add` subcommand (SKILL.md lines 69–76) hard-codes worktree
path derivation: it takes `<repo-root>/../<repo-name>-<slug>` — always a sibling of the
repository. There is no way for users to redirect worktrees to a different root directory.

The project uses JSON for all config files (`settings.json`, `settings.local.json`,
`plugins/config.json`). The new `worktree-config.json` follows that convention.

No config-reading infrastructure exists today. Each skill reads what it needs directly via
`Read` or `Bash`. The same pattern applies here — no shared helper is introduced.

The `try` agent creates worktrees via `EnterWorktree` independently and is out of scope for
this change.

See `FUNCTIONAL.md` for consumer-visible behavior (file location, format, fallback
semantics, error handling, path resolution rules).

## Proposed changes

### 1 — New file: `~/.claude/worktree-config.json` (user-created)

Document the schema in comments or README. The only key consumed today:

```json
{
  "worktrees_path": "~/worktrees"
}
```

### 2 — Modify `skills/git-worktree/SKILL.md`

**`allowed-tools` addition:**

Add `Bash(mkdir:*)` and `Bash(stat:*)` to support auto-creating the configured path and
checking whether it is a file vs. a directory.

**`add` subcommand — Step 2 (Resolve path)** (currently lines 69–76):

Insert a config-read sub-step before the current default derivation:

```
2a. Attempt Read ~/.claude/worktree-config.json.
    - File missing or unreadable → fall through to 2b (default path).
    - File exists but not valid JSON → report parse error and stop.
    - File exists, valid JSON, but worktrees_path is absent, null, or empty string
      → fall through to 2b (default path).
    - File exists, valid JSON, worktrees_path is a non-empty string → use it as BASE.

    Path resolution for BASE (when found):
    - Expand leading ~ to $HOME.
    - If BASE is still relative, prepend $HOME.
    - stat <BASE>: if it exists and is a file (not a directory) → report error and stop.
    - If BASE does not exist → mkdir -p <BASE>. If mkdir fails (e.g. permission denied)
      → report error and stop.
    - Derive worktree path: <BASE>/<repo-name>-<slug>

2b. Default path (when no valid config or worktrees_path absent):
    Current behavior unchanged — <repo-root>/../<repo-name>-<slug>
```

The confirmation prompt (Step 2, line 78–83) remains unchanged — the user sees and
confirms the resolved path regardless of source.

### Tradeoff: model-parsed vs. shell-parsed JSON

`Read` already returns the file content; the model can extract `worktrees_path` without
shelling out to `python3`. This avoids adding `Bash(python3:*)` to allowed-tools and keeps
the diff minimal. The downside is that model JSON parsing is less strict than a real parser
— but the only value consumed is a single string key, so this is acceptable.

## Testing and validation

**Invariant 1** — create `~/.claude/worktree-config.json` with a valid `worktrees_path`,
run `/git-worktree add <branch>`, confirm the suggested path is `<worktrees_path>/<repo-name>-<slug>`.

**Invariant 2** — confirm `worktrees_path` is the only key read; add extra keys to the
JSON and verify they do not affect the resolved path.

**Invariant 3** — delete `worktrees_path` from the config; verify skill falls back to the
sibling-directory default.

**Invariants 4, 12** — write a config file with invalid JSON / make it unreadable (`chmod
000`); verify the skill reports the error and stops rather than silently falling back.

**Invariants 5, 6** — set `worktrees_path` to a relative path (`worktrees/my`) and to a
`~`-prefixed path (`~/worktrees`); verify both expand correctly.

**Invariant 7** — set `worktrees_path` to a directory that does not yet exist; run `add`;
verify the directory is created before the worktree.

**Invariant 8** — make `worktrees_path` non-creatable (parent not writable); verify the
skill reports the error and does not fall back to the default.

**Invariant 9** — verify the worktree lands inside `worktrees_path` (as a subdirectory)
not at `worktrees_path` itself.

**Invariant 10** — set `worktrees_path` to `""`; verify fallback to default.

**Invariant 11** — create a file (not a directory) at the `worktrees_path` value; verify
the skill reports the conflict and stops.

## Follow-ups

- The `try` agent may benefit from the same config once its worktree path is user-visible.
- If multiple skills eventually read this config, extracting a shared read-and-validate
  script (e.g. `scripts/read-worktree-config.sh`) would reduce duplication.
