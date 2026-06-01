# Derive PR Content — Subagent Prompt

This prompt is shared by `git-pr` and `git-pr-update`. Both skills should read this file
and pass its contents verbatim as the subagent prompt. If you update this prompt, update
the copy in `git-pr/SKILL.md` Step 1 as well (or migrate it to use this reference too).

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
