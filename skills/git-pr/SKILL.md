---
name: git-pr
description: >
  Use this skill to create a Bitbucket pull request from the current branch.
  Invoke when the user says "create a PR", "open a pull request", "submit a PR",
  "raise a pull request", or similar. Requires BITBUCKET_TOKEN in the environment.
  Handles base-branch detection, title/description drafting, preview, and API submission.
version: 1.0.0
disable-model-invocation: false
allowed-tools: Bash(git rev-parse:*) Bash(git log:*) Bash(git remote:*) Bash(bash ~/.claude/skills/git-pr/scripts/:*) Write
---

## Available scripts

- `~/.claude/skills/git-pr/scripts/create-pr.sh` — writes JSON payload and POSTs to the Bitbucket API. Run `--help` to confirm the interface.

## Abort conditions

Stop immediately and tell the user if:
- The repository remote is not a Bitbucket URL (`bitbucket.org` not present in `git remote get-url origin`).
- The current branch is `main`, `master`, `develop`, or `trunk` — these are shared branches; creating a PR from them is almost certainly wrong.

## Step 1 — Pre-flight

Run each command separately. Never chain with `&&`, `||`, or `;`.

1. `git rev-parse --abbrev-ref HEAD` → **source branch**. Apply abort conditions above.
2. `git remote get-url origin` → parse **workspace** and **repo-slug**:
   - SSH: `git@bitbucket.org:<workspace>/<repo-slug>.git`
   - HTTPS: `https://bitbucket.org/<workspace>/<repo-slug>.git`
   If the URL does not match either pattern, stop: "Cannot parse workspace/repo from remote URL: `<url>`. Is this a Bitbucket repository?"

## Step 2 — Detect base branch

Run:
```
git log -g --format="%gs" <source-branch>
```

Scan output for a line matching `branch: Created from <name>`. Use `<name>` as the **base branch**.

If no such line is found, fall back to `main`. If `main` is also the source branch, fall back to `develop`. If that is also the source branch, stop and ask the user which branch to target.

## Step 3 — Collect commits

First, resolve the base branch ref. Run:
```
git rev-parse --verify <base-branch>
```

If that exits non-zero (local branch does not exist), use `origin/<base-branch>` as the ref for the remaining steps. Otherwise use `<base-branch>`.

Then run both separately (using the resolved ref):
```
git log <resolved-ref>..HEAD --oneline
git log <resolved-ref>..HEAD --format="%s%n%b"
```

If the first command returns no output, stop: "No commits found between `<base-branch>` and `<source-branch>`. Nothing to PR."

## Step 4 — Draft title and description

From the commit subjects and bodies:

- **Title**: Conventional Commits style (e.g. `feat(scope): summary`), under 70 characters. Synthesize across all commits — do not copy the most recent subject verbatim unless it accurately covers everything.
- **Description** (use this template):

```
## What is the purpose of this PR?
<!-- Context and motivation — why this is being done, not just what it does -->

## What changes concretely?
- <one bullet per logical change>

## Where should reviewers start?
<!-- Entry point or file that provides the most context -->

## How were these changes tested?
- <describe what was run, e.g. unit tests, manual verification, staging deploy>

## Does this deployment introduce any risk?
<!-- Migrations, env vars, feature flags, rollback considerations — or "None" -->
```

## Step 5 — Preview and confirm

Show exactly this block, then wait for the user's choice:

```
PR preview:
  From:  <source-branch>
  Into:  <base-branch>
  Repo:  <workspace>/<repo-slug>

  Title: <title>

  <description>

(a) Create PR
(b) Edit title
(c) Edit description
(d) Abort
```

- **(b)**: Ask "Enter new title:" — update, re-show the preview.
- **(c)**: Ask "Enter new description (markdown):" — update, re-show.
- **(d)**: Stop. Output: `PR creation aborted.`
- **(a)**: Proceed to Step 6.

## Step 6 — Create the PR

Use the `Write` tool to write the description to `/tmp/_pr_description.txt` with the exact description content (no extra escaping needed).

Run `--help` on the script first to confirm flags, then invoke:
```bash
bash ~/.claude/skills/git-pr/scripts/create-pr.sh \
  --workspace "<workspace>" \
  --repo "<repo-slug>" \
  --source "<source-branch>" \
  --destination "<base-branch>" \
  --title "<title>" \
  --description-file /tmp/_pr_description.txt
```

## Step 7 — Report result

The script outputs the JSON response body followed by `status=<value>` on the last line.

- `status=created` → show: `PR created: https://bitbucket.org/<workspace>/<repo-slug>/pull-requests/<id>`
- `status=unauthorized` → Token is invalid or expired. Tell the user to regenerate it.
- `status=forbidden` → Token lacks `write:pullrequest:bitbucket` scope.
- `status=error` → Show the `"message"` field from the JSON response prefixed with `Error:`.
