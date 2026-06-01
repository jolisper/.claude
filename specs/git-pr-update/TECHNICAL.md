# git-pr-update — Technical Plan

## Context

This skill is new — no existing files to modify. It lives entirely in two new files:

| File | Role |
|---|---|
| `skills/git-pr-update/SKILL.md` | Skill definition: instructions Claude follows at runtime |
| `skills/git-pr-update/scripts/update-pr.sh` | Shell script: PATCHes the Bitbucket PR via API |

The closest analog is `skills/git-pr/` (`SKILL.md` + `scripts/create-pr.sh`). Both skills share:
- The same Bitbucket API auth pattern (`BITBUCKET_TOKEN` / `BITBUCKET_USERNAME` basic auth).
- The same subagent drafting flow (git log → Conventional Commits title + structured description).
- The same script output contract: JSON response body on stdout, then `status=<value>` on the last line.
- The same `disable-model-invocation: true` + explicit `allowed-tools` frontmatter style.

The only novel pieces are: querying for an existing PR by branch name, and using `PUT` instead of `POST`.

## Proposed changes

### `skills/git-pr-update/scripts/update-pr.sh`

Model directly on `create-pr.sh` (`skills/git-pr/scripts/create-pr.sh`). Differences:

- **Flags**: `--workspace W --repo R --pr-id N --title T --description-file F` (no `--source` / `--destination`).
- **Endpoint**: `PUT https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests/{id}`.
- **Payload**: `{"title": ..., "description": ...}` — always both fields (invariant 19).
- **Status mapping**: HTTP 200 → `status=updated` (vs. 201 → `status=created` in create-pr.sh).

Keep everything else identical to `create-pr.sh`: `set -euo pipefail`, python3 for JSON payload, curl `-s -w "\n%{http_code}"`, same env var validation block, same `--help` usage string.

### `skills/git-pr-update/SKILL.md`

Frontmatter mirrors `git-pr/SKILL.md`:

```yaml
name: git-pr-update
description: >
  Use this skill to update the title and/or description of an existing open Bitbucket
  pull request for the current branch. Invoke when the user says "update the PR",
  "refresh the PR description", "fix the PR title", or similar.
  Requires BITBUCKET_TOKEN and BITBUCKET_USERNAME in the environment.
version: 1.0.0
disable-model-invocation: true
allowed-tools: Agent AskUserQuestion Bash(bash:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git remote:*) Bash(git show:*) Write
```

**Step 0 — Pre-flight** (invariants 1–3)
Same abort-early block as `git-pr/SKILL.md`: check branch name against shared-branch list, check remote URL for `bitbucket.org`, check env vars.

**Step 1 — PR auto-detection** (invariants 4–7)
Query the Bitbucket API directly from SKILL.md (no subagent needed — it's a single curl):

```bash
curl -s -u "${BITBUCKET_USERNAME}:${BITBUCKET_TOKEN}" \
  "https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests\
?q=source.branch.name%3D%22{branch}%22+AND+state%3D%22OPEN%22"
```

Parse `values` from the JSON response. The workspace and repo-slug come from `git remote get-url origin` using the same SSH/HTTPS parse logic as in the `git-pr` drafting subagent.

- 0 results → stop (invariant 5).
- 1 result → proceed with `PR_ID`, `PR_TITLE`, `PR_DESCRIPTION`, `PR_URL` (invariant 6).
- 2+ results → list them and use `AskUserQuestion` to let the user pick (invariant 7). In `--auto` mode, stop instead (invariant 32).

**Step 2 — Mode selection** (invariants 8–9)
Show current title + description, then present the five choices via `AskUserQuestion`. Skip entirely in `--auto` mode (invariant 28).

**Step 3 — Re-derive or edit** (invariants 10–15)

- **Option (a) / auto mode**: Launch the same subagent prompt as `git-pr/SKILL.md` Step 1 (sections A–D verbatim). The subagent already detects the base branch and commit range on its own; parse `TITLE` and `DESCRIPTION` from its output. If the subagent returns `ERROR:`, stop (invariant 12).
- **Options (b/c/d)**: Prompt with `AskUserQuestion` for the field(s); preserve the other field from the fetched PR.

**Step 4 — Preview and confirm** (invariants 16–17)
Show the PR update preview block and offer (a) Update / (b) Edit title / (c) Edit description / (d) Abort via `AskUserQuestion`. Skip in `--auto` mode (invariant 29).

**Step 5 — Run the script** (invariants 18–19)
Write description to `/tmp/_pr_update_description.txt` with the `Write` tool, then:

```bash
bash ~/.claude/skills/git-pr-update/scripts/update-pr.sh \
  --workspace "<WORKSPACE>" \
  --repo "<REPO>" \
  --pr-id "<PR_ID>" \
  --title "<TITLE>" \
  --description-file /tmp/_pr_update_description.txt
```

Run `--help` first to confirm flags (same convention as `git-pr`). Stop on non-zero exit.

**Step 6 — Report result** (invariants 20–23, 33)
Same status dispatch as `git-pr`: parse `status=` from the last output line and report accordingly. `status=updated` → `PR updated: <url>`.

**`--auto` flag handling** (invariants 28–33)
SKILL.md should check for `--auto` in `$SKILL_ARGS` (or equivalent) at the top and set a variable that gates the `AskUserQuestion` calls in Steps 2 and 4. No other logic changes.

## Diagram

```
Invoke /git-pr-update [--auto]
        │
        ▼
   Pre-flight (branch, remote, env vars)
        │ pass
        ▼
   Fetch open PRs for branch via API
        ├─ 0 found → stop
        ├─ 1 found → proceed
        └─ 2+ found ──┬─ interactive: AskUserQuestion (pick PR)
                      └─ auto: stop (ambiguous)
        │
        ▼
   [interactive] Show current title+desc, AskUserQuestion (a/b/c/d/e)
   [auto]        skip → option (a)
        │
        ├─ (a) subagent: git log → draft title + description
        ├─ (b) AskUserQuestion: new title
        ├─ (c) AskUserQuestion: new description
        ├─ (d) AskUserQuestion: title, then description
        └─ (e) abort
        │
        ▼
   [interactive] Preview → AskUserQuestion (a/b/c/d)
   [auto]        skip
        │
        ▼
   Write desc to /tmp, run update-pr.sh
        │
        ▼
   Report PR updated: <url>  |  error
```

## Testing and validation

Skills have no automated test runner; all validation is manual. Each invariant maps to a specific verification step.

| Invariants | Verification |
|---|---|
| 1–3 (pre-flight) | Run on `main`; run pointed at a non-Bitbucket remote; run with `BITBUCKET_TOKEN` unset. Confirm each stops with the correct message. |
| 4–7 (PR detection) | Run on a branch with no open PR (expect stop). Run on a branch with one open PR (expect auto-select). Manually create two PRs for the same branch to verify the list+pick path. |
| 8–9 (mode selection) | Invoke interactively; verify all five menu options are shown and (e) aborts cleanly. |
| 10–12 (re-derive) | Choose (a) with commits present; verify draft reflects commit messages. Check out a branch with no commits ahead of base; verify stop with error message. |
| 13–15 (manual edit) | Exercise (b), (c), (d) and confirm the untouched field matches the original PR exactly. |
| 16–17 (preview) | Confirm preview block displays before any PATCH is sent. Choose (b)/(c) from preview and verify re-entry into edit flow. |
| 18–19 (API call) | Inspect `update-pr.sh` output: confirm both `title` and `description` appear in the payload JSON even when only one changed. |
| 20–23 (result reporting) | Force 401 (bad token), 403 (wrong scope), and non-200 response to verify each error message. Successful update: confirm reported URL opens the correct PR. |
| 24 (no silent PATCH) | In interactive mode, verify no PATCH is issued without a confirmation AskUserQuestion. |
| 25 (abort leaves PR unchanged) | Abort at mode selection and at preview; confirm PR title/description on Bitbucket is unmodified. |
| 26 (no PR number input) | Verify SKILL.md contains no step asking the user for a PR number. |
| 27 (show current before editing) | In all manual edit modes, verify current title+description are displayed before the prompt. |
| 28–33 (auto mode) | Run `--auto` on a clean branch: confirm menu and preview are skipped and PR is updated. Run `--auto` on empty commit range: confirm stop without update. Run `--auto` on branch with 2 open PRs: confirm stop with ambiguity message. |
