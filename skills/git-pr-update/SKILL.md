---
name: git-pr-update
description: >
  Use this skill to update the title and/or description of an existing open Bitbucket
  pull request for the current branch. Invoke when the user says "update the PR",
  "refresh the PR description", "fix the PR title", "sync the PR", or similar.
  Requires BITBUCKET_TOKEN and BITBUCKET_USERNAME in the environment.
version: 1.0.0
disable-model-invocation: true
allowed-tools: Agent AskUserQuestion Bash(bash:*) Bash(git rev-parse:*) Bash(git log:*) Bash(git remote:*) Bash(git show:*) Write
---

**Important**: Never use `cd`, `git -C`, `&&`, `||`, or `;`. Run each command separately with no path arguments — rely on the shell's current working directory.

Check whether `--auto` was passed in the invocation arguments. If yes, set AUTO=true; otherwise AUTO=false. AUTO=true skips the mode selection menu and the preview confirmation step.

## Abort early if

- The current branch is `main`, `master`, `develop`, or `trunk` — these are shared branches.
- The `origin` remote URL is not a `bitbucket.org` URL — this skill only targets Bitbucket.
- `BITBUCKET_TOKEN` or `BITBUCKET_USERNAME` are not set in the environment.

If any condition applies, stop immediately and explain the reason.

## Step 1 — Detect workspace, repo, and branch

Run each separately:

```
git rev-parse --abbrev-ref HEAD
```
→ SOURCE_BRANCH. Stop if it is `main`, `master`, `develop`, or `trunk`.

```
git remote get-url origin
```
→ parse WORKSPACE and REPO:
- SSH: `git@bitbucket.org:<workspace>/<repo>.git`
- HTTPS: `https://bitbucket.org/<workspace>/<repo>.git`

Stop if `bitbucket.org` is not present or the URL matches neither pattern.

## Step 2 — Find the open PR

Run:

```bash
curl -s -u "${BITBUCKET_USERNAME}:${BITBUCKET_TOKEN}" \
  "https://api.bitbucket.org/2.0/repositories/${WORKSPACE}/${REPO}/pullrequests?q=source.branch.name%3D%22${SOURCE_BRANCH}%22%2BAND%2Bstate%3D%22OPEN%22"
```

Parse the `values` array from the JSON response:

- **0 results** → stop: `No open PR found for branch '<SOURCE_BRANCH>'.`
- **1 result** → extract PR_ID, PR_TITLE, PR_DESCRIPTION, PR_URL. Proceed.
- **2+ results** → if AUTO=false: list them (id, title, creation date) and use `AskUserQuestion` to let the user pick one. If AUTO=true: stop with `Multiple open PRs found for branch '<SOURCE_BRANCH>' — run without --auto to pick one.`

## Step 3 — Choose update mode

**If AUTO=true**: skip this step. Proceed to Step 4 with mode=(a).

**If AUTO=false**: display the current PR title and description, then present this menu via `AskUserQuestion`:

```
Current PR: #<PR_ID> — <PR_URL>

Title:
<PR_TITLE>

Description:
<PR_DESCRIPTION>

How do you want to update this PR?
(a) Re-derive title and description from commits
(b) Edit title only
(c) Edit description only
(d) Edit both manually
(e) Abort
```

On **(e)**: stop. Output: `PR update aborted.`

## Step 4 — Produce new title and description

### Mode (a) — Re-derive from commits (also used when AUTO=true)

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
- <describe what was run — commands, test suites, or manual verification.>

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

Parse NEW_TITLE and NEW_DESCRIPTION from the subagent output. The existing PR content does not influence the draft.

### Mode (b) — Edit title only

Show the current title. Use `AskUserQuestion` to prompt: `Enter new title:`.
Set NEW_TITLE to the user's reply. Set NEW_DESCRIPTION to PR_DESCRIPTION (unchanged).

### Mode (c) — Edit description only

Show the current description. Use `AskUserQuestion` to prompt: `Enter new description (markdown):`.
Set NEW_DESCRIPTION to the user's reply. Set NEW_TITLE to PR_TITLE (unchanged).

### Mode (d) — Edit both manually

Use `AskUserQuestion` to prompt: `Enter new title:`. Set NEW_TITLE.
Use `AskUserQuestion` to prompt: `Enter new description (markdown):`. Set NEW_DESCRIPTION.

## Step 5 — Preview and confirm

**If AUTO=true**: skip this step. Proceed directly to Step 6.

**If AUTO=false**: show the full proposed update and ask for confirmation via `AskUserQuestion`:

```
PR update preview:
  Repo:  <WORKSPACE>/<REPO>
  PR:    #<PR_ID> — <PR_URL>

  Title: <NEW_TITLE>

  <NEW_DESCRIPTION>

(a) Update PR
(b) Edit title
(c) Edit description
(d) Abort
```

- **(b)**: prompt `Enter new title:` — update NEW_TITLE, re-show preview.
- **(c)**: prompt `Enter new description (markdown):` — update NEW_DESCRIPTION, re-show preview.
- **(d)**: stop. Output: `PR update aborted.`
- **(a)**: proceed to Step 6.

## Step 6 — Update the PR

Use the `Write` tool to write NEW_DESCRIPTION to `/tmp/_pr_update_description.txt`.

Run `--help` on the script first to confirm flags, then invoke:

```bash
bash ~/.claude/skills/git-pr-update/scripts/update-pr.sh \
  --workspace "<WORKSPACE>" \
  --repo "<REPO>" \
  --pr-id "<PR_ID>" \
  --title "<NEW_TITLE>" \
  --description-file /tmp/_pr_update_description.txt
```

If the script exits non-zero, show the error output and stop.

## Step 7 — Report result

The script outputs the JSON response body followed by `status=<value>` on the last line.

- `status=updated` → show: `PR updated: <PR_URL>`
- `status=unauthorized` → Token is invalid or expired. Tell the user to regenerate it.
- `status=forbidden` → Token lacks `write:pullrequest:bitbucket` scope.
- `status=error` → Show the `"message"` field from the JSON response prefixed with `Error:`.
