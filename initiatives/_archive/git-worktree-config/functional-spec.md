# git-worktree-config

## Summary

A JSON configuration file at `~/.claude/worktree-config.json` that lets Claude Code users specify the directory where git worktrees are created. Consumed by skills and tools that create worktrees on behalf of the user.

## Behavior

### Reading the config

1. When a consumer reads the config, it looks for `~/.claude/worktree-config.json`. If the file does not exist, the consumer falls back to a default worktrees path (e.g. `~/worktrees`).
2. The config file is a JSON object. The `worktrees_path` key specifies the directory where worktrees are created. All other keys are ignored.
3. If the file exists but `worktrees_path` is absent or null, the consumer behaves as if the file does not exist (fallback to default).
4. If the file exists but is not valid JSON, the consumer reports a parse error and stops — it does not fall back silently.
5. If `worktrees_path` is a relative path, it is resolved relative to `~` (the user's home directory).
6. If `worktrees_path` contains `~`, it is expanded to the user's home directory before use.

### Using the configured path

7. When a worktree is created and `worktrees_path` refers to a directory that does not yet exist, the consumer creates it (equivalent to `mkdir -p`) before placing the worktree inside.
8. If the consumer cannot create the directory (e.g. permission denied), it reports the error and stops — it does not fall back to the default path.
9. Worktrees are placed inside `worktrees_path`, not at `worktrees_path` itself. The worktree directory name is determined by the consumer.

### Edge cases

10. If `worktrees_path` is an empty string, the consumer treats it as absent and falls back to the default.
11. If `worktrees_path` points to an existing file (not a directory), the consumer reports an error and stops.
12. If `~/.claude/worktree-config.json` is not readable (e.g. permissions), the consumer reports the error and stops — it does not silently fall back.
