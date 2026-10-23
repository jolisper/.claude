# ~/.claude
Personal Claude Code configuration — skills, agents, and settings.

## Skills

Skills marked **Model-invocable: yes** can be invoked by Claude when context matches; **no** means they only run when you type `/skill-name`.

### Git

| Skill | What it does | Model-invocable |
|---|---|---|
| `/git-status` | Concise working-tree overview with branch hierarchy | yes |
| `/git-log` | View or search recent commit history | yes |
| `/git-diff` | Summarize uncommitted changes and check coherence | yes |
| `/git-commit` | Stage + commit with Conventional Commits message | no |
| `/git-push` | Push to remote, handles divergence and rebases | no |
| `/git-commit-push` | Stage → commit → push in one workflow | no |
| `/git-pull` | Pull with guided merge-conflict resolution | yes |
| `/git-rebase` | Rebase onto base branch with conflict resolution | no |
| `/git-merge` | Merge a branch, strictly fast-forward only (diverged → rebase first) | no |
| `/git-new-branch` | Create a branch from latest main/master; auto mode infers the name from context (`--no-auto` for menus) | no |
| `/git-reshape` | Regroup, split, squash and reword branch commits into a coherent functional history | no |
| `/git-worktree` | Add, list, remove, prune and close out worktrees; context-aware inside a worktree | no |
| `/git-pr` | Create a Bitbucket or GitHub pull request from the current branch | no |
| `/git-pr-update` | Update title/description of an existing Bitbucket or GitHub PR | no |

Bitbucket needs `BITBUCKET_TOKEN` and `BITBUCKET_USERNAME`; GitHub needs an authenticated `gh` CLI.

### Session

| Skill | What it does | Model-invocable |
|---|---|---|
| `/unbranch` | Return to the conversation this session was `/branch`ed from (copies `/resume` command to clipboard) | no |
| `/recap` | Print a concise session recap | yes |

### Project

| Skill | What it does | Model-invocable |
|---|---|---|
| `/test-run-all` | Detect project type, clean artifacts, run tests | yes |
| `/refactor` | Refactor following Object Calisthenics rules | no |
| `/sdk` | Switch SDKMAN-managed SDK version (Java, Node, …) | yes |
| `/try` | Investigate a solution in an isolated worktree | no |

### TDD

| Skill | What it does | Model-invocable |
|---|---|---|
| `/tdd-spec` | Turn a short objective (or existing spec) into a gap-free spec for `/tdd-session` | no |
| `/tdd-session` | Autonomous TDD session: drives red-green-refactor cycles until the goal is fully implemented; accepts an optional spec file | yes |
| `/tdd-cycle` | Single red-green-refactor loop: asks for the next behavior, drives the cycle, then stops | no |
| `/tdd-compact` | Compact accumulated lessons in `~/.claude/tdd/lessons/` into one per category | no |

The cycles are driven by the `tdd-auto`, `tdd-red`, `tdd-green` and `tdd-refactor` agents (see [Agents](#agents)).

### Obsidian

Notes live in a configured vault; run `/obsidian-vault` once first.

| Skill | What it does | Model-invocable |
|---|---|---|
| `/obsidian-vault` | Configure and initialize the vault | no |
| `/obsidian-capture` | Capture session context as a note (explicit request only) | yes |
| `/obsidian-literal` | Save content verbatim, no rewriting | no |
| `/obsidian-update` | Append content to an existing note by ID | yes |
| `/obsidian-search` | Search the vault by `#tag` and/or keyword | yes |
| `/obsidian-journal` | Write an end-of-day journal entry (one note per day) | no |
| `/obsidian-log` | Toggle the Stop-hook session log to Obsidian | no |

### Meta

| Skill | What it does | Model-invocable |
|---|---|---|
| `/skill-create` | Scaffold a new skill from scratch | no |
| `/skill-improve` | Audit and improve an existing skill | no |
| `/skill-update` | Apply a feature or behavior change to an existing skill, checking for scope creep | no |
| `/agent-improve` | Audit and improve an existing agent | no |
| `/memory-list` | List all auto-memory entries for the current project | no |
| `/memory-manage` | Review, edit, remove, or archive memory entries | no |
| `/memory-archive` | Inspect and restore/remove orphaned memory files | no |

### Utilities

| Skill | What it does | Model-invocable |
|---|---|---|
| `/english-tutor` | Toggle the [english-tutor mod](#mods), switch strict mode, review logged mistakes | no |
| `/voiceink-en` | Switch VoiceInk transcription to English | no |
| `/voiceink-es` | Switch VoiceInk transcription to Spanish | no |
| `/warp-theme-from-macos` | Generate a Warp theme from the active macOS aerial wallpaper | no |

## Spec workflow

The `spec-*` family models a full agent-driven software workflow: **intent → behavior spec → technical plan → TDD implementation → verification → archive**. Each stage produces a file under `initiatives/<name>/`, and each stage is explicitly user-invoked so a human reviews every hand-off.

```
/spec-initiative  →  initiative.md          why: problem, goals, non-goals, scope
/spec-functional  →  functional-spec.md     what: numbered behavior invariants (auto-reads initiative.md)
/spec-partition   →  split functional specs (optional, for large specs)
/spec-technical   →  technical-spec.md      how: codebase-grounded implementation plan
/spec-implement   →  code + logbook.md      phased build: scaffolding agent + TDD cycles
/spec-verify-static  →  report              does every invariant have test coverage?
/spec-verify-dynamic →  report              does every invariant hold in the running app?
/spec-archive     →  initiatives/_archive/<name>/
```

| Skill | Role |
|---|---|
| `/spec-initiative` | Creates `initiative.md` and the initiative branch from `origin/main`. Free prose, no invariants |
| `/spec-functional` | Behavioral spec from the consumer's perspective, as numbered invariants. Required input for everything downstream |
| `/spec-partition` | Splits a large functional spec (≳30 invariants or unrelated concerns) into an ordered chain of independently implementable specs, without adding, removing or rewording any invariant |
| `/spec-technical` | Researches the codebase and turns the functional spec into an implementation plan. Stops if no functional spec exists |
| `/spec-implement` | Orchestrator only: decomposes the plan into phases, classifies each as scaffolding (setup agent) or TDD (red-green-refactor via the `tdd-*` agents), and keeps a master log. It never writes code itself |
| `/spec-verify-static` | Greps tests for each invariant and reports covered/uncovered. No app launch |
| `/spec-verify-dynamic` | Launches the app through a project run recipe (`.claude/skills/run-*/`), exercises each invariant, reports pass/fail. Stops if no recipe exists |
| `/spec-archive` | Checks completeness and uncommitted changes, appends a retrospective, moves the initiative to `initiatives/_archive/` |

The family is biased toward code projects. For non-code work (config, skills, prose), use only `/spec-initiative` + `/spec-functional` and pass the result to `/skill-create`. Active and archived initiatives live in `initiatives/`.

## Agents

| Agent | Purpose |
|---|---|
| `architect` | Critique designs or produce architecture specs; escalates via AskUserQuestion when trade-offs need a human decision |
| `try` | Investigate and experiment in an isolated worktree; produces a structured try-report in `docs/try-agent/` |
| `tdd-auto` | Autonomous TDD orchestrator: finds the middle of the problem, then drives red-green-refactor one behavior at a time |
| `tdd-red` | Writes exactly one failing test for a behavior and verifies it fails |
| `tdd-green` | Writes the minimum implementation to pass the failing test; never touches tests |
| `tdd-refactor` | Cleans up after green without new behavior; keeps tests green |

## Mods

`mods/` is a plugin marketplace (`jolisper-mods`) holding Claude Code mods.

### english-tutor

Corrects non-native English phrasing in submitted prompts via an isolated model call (TypeScript hooks in `mods/english-tutor/hooks/`).

- Classifies each correction as **error** or **style** and shows it as a toast instead of leaking it into the conversation context.
- **Strict mode** blocks the prompt until you retry with a corrected version; unchanged retries are rejected and only the first consecutive style-only correction blocks. **Lenient mode** only informs.
- Ignores a lowercase first letter and agent hand-back messages.
- Logs checked prompts (with session id) to daily JSONL files in `~/.english-tutor/logs/`; `/english-tutor` reviews mistakes and gives recommendations.
- Defaults to disabled when absent from settings; toggle with `/english-tutor`.

## Setup

After cloning, run the setup script once to apply the required settings to your local config:

```bash
bash scripts/apply-settings-template.sh
```

This merges `settings.template.json` into `settings.json`. On conflict it prompts you key by key — you can keep your current value, adopt the template value, or skip. The status line won't work without the `statusLine` key, so the script will warn you if you skip it.

## Status Line

A custom status line rendered by `statusline/command.sh`. Wired up via `settings.template.json`.

**Dependencies:** `jq`, `awk`, `git`, `sed` — all must be available on `PATH`.

```json
"statusLine": { "type": "command", "command": "sh ~/.claude/statusline/command.sh" }
```

**Example:**

![Status line screenshot](docs/assets/statusline.png)

---

Format: `dirname (branch*? +N/-N) | [^model] ▓▓░░ ctx% (cache%) | rate_5h%(reset) rate_7d%(reset) | ~sess wall (api think%)`

| Segment | Default | Description |
|---|---|---|
| `time` | off (script default: on) | Current time (`HH:MM`) |
| `branch` | on | Git branch + dirty flag (`*`) + diff stats (`+N/-N`) |
| `model` | on | Running model in brackets with cloud/local indicator (`^` = cloud, `~` = local/Ollama); a `(d)` marker means the default model (not available for resumed sessions) |
| `ctx_bar` | on | Color-coded progress bar + context % used |
| `cache_pct` | on | Cache hit ratio in parentheses (Ollama KV cache hit % in local mode) |
| `coherence_warning` | on | Blinking red dot when context > 50% and cache < 20% |
| `rate_limits` | on | 5-hour and 7-day rate limit usage + time to reset |
| `sess_duration` | on | Elapsed wall time since first prompt (`~Xm Ys`) |
| `wall_time` | on | Cumulative API wall time |
| `api_duration` | on | Total API round-trip time |
| `think_pct` | on | Thinking time as % of wall time |
| `lines` | off | Lines added/removed this session |
| `cost` | off | Session cost in USD |

Shared toggles live in `statusline/statusline.conf` (tracked). Personal overrides go in `statusline/statusline.local.conf` (not tracked).

## Settings workflow

**Policy**: `settings.json` is shared config only — `permissions`, `hooks`, and `statusLine`. Everything personal (model, theme, verbosity) goes in `settings.local.json` and is never committed.

The challenge is that Claude Code writes all settings to `settings.json` regardless of their nature, so UI changes will silently accumulate personal keys there. The whitelist + migration step enforces the policy automatically: before a commit, any non-whitelisted key is evicted from `settings.json` and moved to `settings.local.json`. This means it doesn't matter how a setting got into `settings.json` — the contract holds.

### Files

| File | Tracked | Purpose |
|---|---|---|
| `settings.json` | no (normally) | Full working config — shared + personal keys merged |
| `settings.local.json` | no | Personal-only overrides (model, theme, etc.) — takes precedence over `settings.json` |
| `settings.template.json` | yes | Repo-required settings (`statusLine`, `hooks`) — applied via `apply-settings-template.sh` |
| `scripts/apply-settings-template.sh` | yes | Merges `settings.template.json` into `settings.json`, prompting on conflicts |
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

## Hooks and permissions

`settings.template.json` wires:

- **Stop** — `obsidian-log` session logger.
- **UserPromptSubmit** — records the session start time (for the status line), resets Ollama session state (`scripts/ollama-session-reset.sh`), and runs `scripts/english-tutor.py` (legacy hook; superseded by the mod).
- **Deny rules** — blocks reading `~/.ssh`, `~/.gnupg`, `~/.netrc`, `~/.aws`, `~/.git-credentials` and `~/.config`.

## Repository layout

`.gitignore` is an allowlist (everything ignored by default). Tracked: `agents/`, `skills/`, `scripts/`, `statusline/`, `mods/`, `initiatives/`, `docs/`, `specs/`, `commands/`, plus `CLAUDE.md`, `README.md`, `TODO.md` and `settings.template.json`. `docs/` holds notes such as `backup-enforcement.md` and `git-filter-repo-working-tree-reset.md`.
