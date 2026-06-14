# Initiative: git-pr-update skill

## Summary

A new `/git-pr-update` skill that updates the title and/or description of an existing open Bitbucket PR for the current branch — without requiring the user to supply a PR number.

## Origin

The current `/git-pr` skill only creates PRs. After adding commits to a branch post-PR-creation (e.g. fixing review feedback, adding a bug fix to the same branch), the PR description goes stale. Today the only workaround is a manual API call or editing in the Bitbucket UI. This skill automates that update path.

Triggered by a real session where a PR's description had to be manually updated via a raw `curl` after a second commit landed on the same branch.

## Design

### Auto-detection of the PR

No PR number input required. The skill calls the Bitbucket API to find the open PR whose source branch matches the current branch:

```
GET /2.0/repositories/{workspace}/{repo}/pullrequests
    ?q=source.branch.name="{branch}"AND+state="OPEN"
```

If no open PR is found, report and stop. If multiple are found (unusual), list them and ask the user to pick.

### Update modes

After fetching the current PR, show the current title and description, then offer:

```
(a) Re-derive title and description from commits
(b) Edit title only
(c) Edit description only
(d) Edit both manually
(e) Abort
```

Option (a) reuses the same forked subagent prompt from `/git-pr` Step 1 (git log, draft Conventional Commits title + description template). The result is shown as a preview before submitting.

### Preview and confirm

Before PATCHing, always show the full updated title + description and ask for confirmation — same pattern as `/git-pr` Step 2.

### Script

New script: `~/.claude/skills/git-pr/scripts/update-pr.sh`

```
update-pr.sh --workspace W --repo R --pr-id N --title T --description-file F
```

PATCHes `PUT /2.0/repositories/{workspace}/{repo}/pullrequests/{id}` with `{"title": ..., "description": ...}`. Outputs the JSON response body + `status=updated|unauthorized|forbidden|error` on the last line — same contract as `create-pr.sh`.

### Abort conditions (same as `/git-pr`)

- Current branch is `main`, `master`, `develop`, or `trunk`.
- `origin` remote is not a `bitbucket.org` URL.
- No open PR found for the current branch.

## Files to create

| Path | Purpose |
|---|---|
| `~/.claude/skills/git-pr-update/SKILL.md` | Skill definition |
| `~/.claude/skills/git-pr-update/scripts/update-pr.sh` | Bitbucket PATCH script |

## Design principles

- No PR number from the user — auto-detect from branch name.
- Always preview before writing — never silent PATCH.
- Option (a) derives title and description from the commit log: Conventional Commits title + structured description template, same output shape as `/git-pr`.
- Same status-line output contract as `create-pr.sh` for consistent error handling.

## Status

- [x] Initiative documented
- [ ] `update-pr.sh` script written and tested
- [ ] `git-pr-update/SKILL.md` written
- [ ] Installed and validated against a real PR update
