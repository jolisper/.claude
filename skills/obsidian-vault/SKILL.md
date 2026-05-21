---
name: obsidian-vault
description: Use this skill to configure and initialize an Obsidian vault for the obsidian skill family. Run once before using obsidian-capture, obsidian-update, or obsidian-search. Invoke when the vault path is not configured, when a skill reports "Obsidian vault not configured", or when pointing the skill family at a new or existing vault.
argument-hint: "[vault-path]"
disable-model-invocation: true
when_to_use: Use before any obsidian-* skill when the vault is not yet configured; invoke when a skill reports "Obsidian vault not configured"; use when setting up a new or existing Obsidian vault for the obsidian skill family.
allowed-tools: Read Glob Bash(mkdir:*) Bash(bash:*) Write
---

Configure and initialize an Obsidian vault for the obsidian skill family. Works with existing vaults and creates new ones. Run once before using any other obsidian-* skill.

Config resolution order (highest priority first):
1. `$OBSIDIAN_VAULT` environment variable
2. `.claude/obsidian-vault.json` in the current directory (project-local)
3. `~/.claude/obsidian-vault.json` (global)

A local config overrides the global one when both exist.

## Protocol

### Step 1 — Resolve vault path

If `$ARGUMENTS` is non-empty, use it as the vault path. Otherwise ask the user to enter the vault path.

Expand `~` to the home directory and resolve the full absolute path.

### Step 2 — Detect vault state

Run `bash -c "test -d '{path}'"` and `bash -c "test -d '{path}/.obsidian'"` as separate calls.

| path exists | .obsidian/ exists | Action |
|-------------|------------------|--------|
| yes | yes | Existing vault — skip to Step 4 |
| yes | no | Directory exists, not yet a vault — go to Step 3b |
| no | — | Path does not exist — go to Step 3a |

### Step 3a — Create new vault (path does not exist)

Ask:

```
{path} does not exist. How do you want to proceed?
(a) Create a new vault here
(b) Cancel
```

On (a): run `mkdir -p {path}`, then continue to Step 3b. On (b): stop.

### Step 3b — Initialize .obsidian/ (directory exists, not yet a vault)

Ask:

```
No .obsidian/ directory found at {path}. How do you want to proceed?
(a) Initialize as a new Obsidian vault
(b) Cancel
```

On (a): run `mkdir -p {path}/.obsidian`, then Write `{}` to `{path}/.obsidian/app.json`. On (b): stop.

### Step 4 — Ensure @tags/ exists

Run `bash -c "test -d '{path}/@tags'"`. If it does not exist, run `mkdir -p {path}/@tags`. Never touch existing contents.

### Step 5 — Choose config scope

Ask:

```
Where should the vault config be saved?
(a) Project-local — .claude/obsidian-vault.json in the current directory (overrides global)
(b) Global — ~/.claude/obsidian-vault.json (applies to all projects)
```

Set `{config_path}` to:
- (a): `{cwd}/.claude/obsidian-vault.json` — if `.claude/` does not exist, run `mkdir -p {cwd}/.claude`
- (b): `~/.claude/obsidian-vault.json`

### Step 6 — Choose vault language

Ask:

```
What language should notes be written in?
Enter an ISO 639-1 code (e.g. en, es, fr, pt). Default: en
```

If the answer is empty, use `en`. Store as LANG.

### Step 7 — Write config pointer

Write to `{config_path}`:

```json
{
  "vault": "{path}",
  "language": "{LANG}"
}
```

### Step 8 — Validate

Run each as a separate Bash call:

1. `bash -c "test -r '{path}'"` — vault is readable
2. `bash -c "test -w '{path}'"` — vault is writable
3. `bash -c "test -d '{path}/.obsidian'"` — .obsidian/ exists
4. `bash -c "test -d '{path}/@tags'"` — @tags/ exists
5. Read `{config_path}` — verify it is valid JSON, `vault` equals the correct path, and `language` is present

If any check fails: report exactly which check failed and what the user must do to fix it. Stop.

### Step 9 — Report

```
✓ Vault configured: {path}
✓ Language: {LANG}
✓ @tags/ ready
✓ Config pointer written to {config_path}
All skills are ready to use.
```

## Failure contract

- **Directory creation fails:** report the mkdir error and stop. Do not proceed to later steps.
- **.obsidian/app.json write fails:** report the Write error and stop.
- **Validation fails:** report the specific failing check (e.g. "vault is not writable — check directory permissions") and stop.
- **Config pointer write fails:** report the error. Recovery: write `{"vault": "{path}"}` manually to `{config_path}`.
