# ~/.claude
Personal Claude Code configuration — skills, agents, and settings.

## Skills

### Git

| Skill | What it does | Model-invocable |
|---|---|---|
| `/git-status` | Concise working-tree overview with branch hierarchy | yes |
| `/git-log` | View or search recent commit history | yes |
| `/git-diff` | Summarize uncommitted changes and check coherence | no |
| `/git-commit` | Stage + commit with Conventional Commits message | yes |
| `/git-push` | Push to remote, handles divergence and rebases | no |
| `/git-pull` | Pull with guided merge-conflict resolution | yes |
| `/git-rebase` | Rebase onto base branch with conflict resolution | no |
| `/git-commit-push` | Stage → commit → push in one workflow | yes |

### Project

| Skill | What it does | Model-invocable |
|---|---|---|
| `/run-tests` | Detect project type and run tests | no |
| `/refactor` | Refactor following Object Calisthenics rules | no |
| `/sdk` | Switch SDKMAN-managed SDK version (Java, Node, …) | yes |
| `/try` | Investigate a solution in an isolated worktree | no |
| `/recap` | Print a concise session recap | no |

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

## Settings workflow

- `settings.json` — tracked base config (shared keys: `permissions`, `hooks`, `statusLine`)
- `settings.local.json` — untracked local overrides (model preferences, etc.)
- `scripts/settings-whitelist.txt` — defines which keys stay in `settings.json`

**To update the shared config:**
```bash
bash scripts/update-settings.sh "chore(settings): <reason>"
```
This runs `migrate-settings.py` (strips non-whitelisted keys), force-adds `settings.json`, commits, then untracks it again — all in one step.
