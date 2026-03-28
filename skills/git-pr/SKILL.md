---
name: git-pr
description: >
  Use this skill to create a Bitbucket pull request from the current branch.
  Invoke when the user says "create a PR", "open a pull request", "submit a PR",
  "raise a pull request", or similar. Requires BITBUCKET_TOKEN in the environment.
  Handles base-branch detection, title/description drafting, preview, and API submission.
  Requires BITBUCKET_TOKEN and BITBUCKET_USERNAME in the environment.
version: 1.0.0
disable-model-invocation: false
allowed-tools: Agent Bash(bash:*) Write
---

## Abort early if

- The current branch is `main`, `master`, `develop`, or `trunk` — these are shared branches.
- The `origin` remote URL is not a `bitbucket.org` URL — this skill only targets Bitbucket.
- There are no commits between the source branch and its detected base — nothing to PR.

If any of these conditions apply, stop immediately and explain the reason to the user.

## Available scripts

- `~/.claude/skills/git-pr/scripts/create-pr.sh` — writes JSON payload and POSTs to the Bitbucket API. Run `--help` to confirm the interface.

## Step 1 — Gather and draft (forked context)

Launch a subagent using the `Agent` tool with `allowed-tools: Bash(git rev-parse:*) Bash(git log:*) Bash(git remote:*) Bash(git show:*)` and the following prompt verbatim:

---
Run the steps below and return the structured output at the end. Use only what the git commands return — do not draw on any prior context.

**A — Pre-flight**

Run each command separately. Never chain with `&&`, `||`, or `;`.

1. `git rev-parse --abbrev-ref HEAD` → source branch.
   - Stop if the branch is `main`, `master`, `develop`, or `trunk`: output `ERROR: source branch is a shared branch (<name>).`
2. `git remote get-url origin` → parse workspace and repo-slug:
   - SSH: `git@bitbucket.org:<workspace>/<repo-slug>.git`
   - HTTPS: `https://bitbucket.org/<workspace>/<repo-slug>.git`
   - Stop if `bitbucket.org` is not present: output `ERROR: remote is not a Bitbucket URL (<url>).`
   - Stop if the URL matches neither pattern: output `ERROR: cannot parse workspace/repo from remote URL (<url>).`

**B — Detect base branch**

Run:
```
git log -g --format="%gs" <source-branch>
```
Scan for a line matching `branch: Created from <name>`. Use `<name>` as the base branch.
If not found, fall back to `main`. If `main` is also the source branch, fall back to `develop`. If that too is the source branch, output `ERROR: cannot determine base branch automatically.`

**C — Collect commits**

Run:
```
git rev-parse --verify <base-branch>
```
If non-zero, use `origin/<base-branch>` as the resolved ref; otherwise use `<base-branch>`.

Then run both separately:
```
git log <resolved-ref>..HEAD --oneline
git log <resolved-ref>..HEAD --format="%s%n%b"
```
If the first returns no output, output `ERROR: no commits found between <base-branch> and <source-branch>.`

**D — Draft title and description**

Using only the commit data above — not any prior context — draft:

- **Title**: Conventional Commits style (e.g. `feat(scope): summary`), under 70 characters. Synthesize across all commits.
- **Description** using this template:

```
## What is the purpose of this PR?
<!-- Context and motivation — why this is being done and what it achieves. Include any notable changes if they are not obvious from the purpose. -->

## Where should reviewers start?
<!-- Entry point or file that provides the most context -->

## How were these changes tested?
- <describe what was run — commands, test suites, or manual verification. Do not include notes about test infrastructure behavior or skip conditions; those belong in the purpose section if anywhere.>

## Does this deployment introduce any risk?
<!-- List migrations, env vars, feature flags, or rollback considerations. If truly none, say "None — all changes are <scope> and do not introduce risk." -->
```

If a commit subject is unclear, run `git show <hash>` to inspect the diff before including a claim.

Return exactly this format:

```
SOURCE: <source-branch>
BASE: <base-branch>
WORKSPACE: <workspace>
REPO: <repo-slug>
TITLE: <title>
DESCRIPTION:
<description markdown>
```
---

If the subagent output starts with `ERROR:`, stop and show the error to the user.

Otherwise parse `SOURCE`, `BASE`, `WORKSPACE`, `REPO`, `TITLE`, and `DESCRIPTION` from the output.

## Step 2 — Preview and confirm

Show exactly this block, then wait for the user's choice:

```
PR preview:
  From:  <SOURCE>
  Into:  <BASE>
  Repo:  <WORKSPACE>/<REPO>

  Title: <TITLE>

  <DESCRIPTION>

(a) Create PR
(b) Edit title
(c) Edit description
(d) Abort
```

- **(b)**: Ask "Enter new title:" — update, re-show the preview.
- **(c)**: Ask "Enter new description (markdown):" — update, re-show.
- **(d)**: Stop. Output: `PR creation aborted.`
- **(a)**: Proceed to Step 3.

## Step 3 — Create the PR

Use the `Write` tool to write the description to `/tmp/_pr_description.txt` with the exact description content (no extra escaping needed).

Run `--help` on the script first to confirm flags, then invoke. If the script exits non-zero, show the error output to the user and stop — do not proceed to Step 4.
```bash
bash ~/.claude/skills/git-pr/scripts/create-pr.sh \
  --workspace "<WORKSPACE>" \
  --repo "<REPO>" \
  --source "<SOURCE>" \
  --destination "<BASE>" \
  --title "<TITLE>" \
  --description-file /tmp/_pr_description.txt
```

## Step 4 — Report result

The script outputs the JSON response body followed by `status=<value>` on the last line.

- `status=created` → show: `PR created: https://bitbucket.org/<WORKSPACE>/<REPO>/pull-requests/<id>`
- `status=unauthorized` → Token is invalid or expired. Tell the user to regenerate it.
- `status=forbidden` → Token lacks `write:pullrequest:bitbucket` scope.
- `status=error` → Show the `"message"` field from the JSON response prefixed with `Error:`.
