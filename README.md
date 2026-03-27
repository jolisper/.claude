# ~/.claude
Personal Claude Code configuration — skills, agents, and settings.

## Skills

### Git

| Skill | What it does | Model-invocable |
|---|---|---|
| `/git-status` | Concise working-tree overview with branch hierarchy | yes |
| `/git-log` | View or search recent commit history | yes |
| `/git-diff` | Summarize uncommitted changes and check coherence | yes |
| `/git-commit` | Stage + commit with Conventional Commits message | no |
| `/git-push` | Push to remote, handles divergence and rebases | no |
| `/git-pull` | Pull with guided merge-conflict resolution | yes |
| `/git-rebase` | Rebase onto base branch with conflict resolution | no |
| `/git-commit-push` | Stage → commit → push in one workflow | yes |

### Project

| Skill | What it does | Model-invocable |
|---|---|---|
| `/run-tests` | Detect project type and run tests | yes |
| `/refactor` | Refactor following Object Calisthenics rules | no |
| `/sdk` | Switch SDKMAN-managed SDK version (Java, Node, …) | yes |
| `/try` | Investigate a solution in an isolated worktree | no |
| `/recap` | Print a concise session recap | yes |

### Meta

| Skill | What it does | Model-invocable |
|---|---|---|
| `/skill-create` | Scaffold a new skill from scratch | no |
| `/skill-improve` | Audit and improve an existing skill | no |
| `/agent-improve` | Audit and improve an existing agent | no |

**Model-invocable: yes** — Claude can invoke the skill automatically when context matches.
**Model-invocable: no** — skill only runs when you explicitly type `/skill-name`.

## Agents

| Agent | Purpose |
|---|---|
| `architect` | Critique designs or produce architecture specs; escalates via AskUserQuestion when trade-offs need a human decision |
| `try` | Investigate and experiment in an isolated worktree; produces a structured try-report in `docs/try-agent/` |

## Setup

After cloning, run the setup script once to apply the required settings to your local config:

```bash
bash scripts/apply-settings-template.sh
```

This merges `settings.template.json` into `settings.local.json`. On conflict it prompts you key by key — you can keep your current value, adopt the template value, or skip. The status line won't work without the `statusLine` key, so the script will warn you if you skip it.

## Status Line

A custom status line rendered by `statusline-command.sh`. Wired up via `settings.template.json`.

**Dependencies:** `jq`, `awk`, `git`, `sed` — all must be available on `PATH`.

```json
"statusLine": { "type": "command", "command": "sh ~/.claude/statusline-command.sh" }
```

**Example:**

![Status line screenshot](docs/assets/statusline.png)

---

Format: `dirname (branch*? +N/-N) | [model] ▓▓░░ ctx% (cache%) | rate_5h%(reset) rate_7d%(reset) | ~sess wall (api think%)`

| Segment | Default | Description |
|---|---|---|
| `time` | off | Current time (`HH:MM`) |
| `branch` | on | Git branch + dirty flag (`*`) + diff stats (`+N/-N`) |
| `model` | on | Active model in brackets (hidden when default) |
| `ctx_bar` | on | Color-coded progress bar + context % used |
| `cache_pct` | on | Cache hit ratio in parentheses |
| `coherence_warning` | on | Blinking red dot when context > 50% and cache < 20% |
| `rate_limits` | on | 5-hour and 7-day rate limit usage + time to reset |
| `sess_duration` | on | Elapsed wall time since first prompt (`~Xm Ys`) |
| `wall_time` | on | Cumulative API wall time |
| `api_duration` | off | Total API round-trip time |
| `think_pct` | off | Thinking time as % of wall time |
| `lines` | off | Lines added/removed this session |
| `cost` | off | Session cost in USD |

Shared toggles live in `statusline.conf` (tracked). Personal overrides go in `statusline.local.conf` (not tracked).

## Settings workflow

**Policy**: `settings.json` is shared config only — `permissions`, `hooks`, and `statusLine`. Everything personal (model, theme, verbosity) goes in `settings.local.json` and is never committed.

The challenge is that Claude Code writes all settings to `settings.json` regardless of their nature, so UI changes will silently accumulate personal keys there. The whitelist + migration step enforces the policy automatically: before a commit, any non-whitelisted key is evicted from `settings.json` and moved to `settings.local.json`. This means it doesn't matter how a setting got into `settings.json` — the contract holds.

### Files

| File | Tracked | Purpose |
|---|---|---|
| `settings.json` | no (normally) | Full working config — shared + personal keys merged |
| `settings.local.json` | no | Personal-only overrides (model, theme, etc.) — takes precedence over `settings.json` |
| `settings.template.json` | yes | Repo-required settings (`statusLine`, `hooks`) — applied via `apply-settings-template.sh` |
| `scripts/apply-settings-template.sh` | yes | Merges `settings.template.json` into `settings.local.json`, prompting on conflicts |
| `scripts/apply-settings-template.py` | yes | Implementation of the above |
| `scripts/settings-whitelist.txt` | yes | Declares which keys are safe to share (`permissions`, `hooks`, `statusLine`) |
| `scripts/migrate-settings.py` | yes | Strips non-whitelisted keys from `settings.json`, moves them to `settings.local.json` |
| `scripts/update-settings.sh` | yes | One-step script: migrate → force-add → commit → untrack |

### Updating the shared config

When you want to commit a change to `permissions`, `hooks`, or `statusLine`, first make sure `scripts/settings-whitelist.txt` includes any new keys you want to share, then run:

```bash
bash scripts/update-settings.sh "chore(settings): <reason>"
```

This does four things in sequence:
1. Runs `migrate-settings.py` — moves any non-whitelisted keys out of `settings.json` into `settings.local.json`
2. Force-adds `settings.json` (bypasses `.gitignore`)
3. Commits with the message you provided
4. Untracks `settings.json` again (`git rm --cached`) so future commits won't touch it

### Personal overrides (settings.local.json)

Do not edit `settings.json` directly for personal preferences. Put model choice, theme, verbosity, and any other personal settings in `settings.local.json` instead. Claude Code merges it on top of `settings.json` at runtime.

If you change a setting through the Claude Code UI, it will land in `settings.json`. Run `migrate-settings.py` to evict it to `settings.local.json` before it can be accidentally committed:

```bash
python3 scripts/migrate-settings.py
```
