# git-pr-update

## Summary

`/git-pr-update` is a CLI skill that updates the title and/or description of an existing open Bitbucket pull request for the current branch, without requiring the user to supply a PR number. The consumer is a CLI user working inside Claude Code on a branch that already has an open PR.

## Problem

After committing follow-up work to a branch (review feedback, bug fixes), the PR title and description go stale. Today the only remedy is a manual `curl` call or editing in the Bitbucket UI. This skill automates that path.

## Behavior

### Pre-flight

1. If the current branch is `main`, `master`, `develop`, or `trunk`, the skill stops immediately and reports that shared branches cannot be updated this way.
2. If the `origin` remote is not a `bitbucket.org` URL, the skill stops and reports the unsupported remote.
3. If `BITBUCKET_TOKEN` or `BITBUCKET_USERNAME` are absent from the environment, the skill stops and instructs the user to set them.

### PR auto-detection

4. The skill queries the Bitbucket API for open PRs whose source branch matches the current branch. It never asks the user for a PR number.
5. If no open PR is found for the current branch, the skill stops and reports that there is no open PR to update.
6. If exactly one open PR is found, it is selected automatically and the skill proceeds.
7. If multiple open PRs are found for the same source branch (unusual), the skill lists them — showing PR id, title, and creation date — and asks the user to pick one before proceeding.

### Update mode selection

8. After finding the PR, the skill displays the current PR title and description, then presents five choices:
   - **(a) Re-derive title and description from commits** — drafts both fields from the commit log.
   - **(b) Edit title only** — prompts the user for a new title; description is unchanged.
   - **(c) Edit description only** — prompts the user for a new description; title is unchanged.
   - **(d) Edit both manually** — prompts for a new title, then a new description.
   - **(e) Abort** — stops with no changes made.
9. Selecting (e) produces the message `PR update aborted.` and makes no API call.

### Re-derive mode (a)

10. The skill reads the commit log between the base branch and `HEAD` and produces a draft title (Conventional Commits style, under 70 characters) and a structured description using the PR template sections (purpose, reviewer entry point, testing, risk). The output is derived solely from the commits — no prior PR content influences the draft.
11. The drafted title and description are shown as a preview before any confirmation is requested — the user sees the full proposed update before committing to it.
12. If the commit range is empty (no commits between base and HEAD), the skill reports the error and stops without updating the PR.

### Manual edit modes (b, c, d)

13. In mode (b), the skill prompts `Enter new title:` and accepts the user's reply as the new title. The existing description is preserved exactly.
14. In mode (c), the skill prompts `Enter new description (markdown):` and accepts the user's reply as the new description. The existing title is preserved exactly.
15. In mode (d), the skill first prompts for the title, then for the description — each in a separate prompt. Both fields are replaced.

### Preview and confirm

16. Before making any API call, the skill displays the full proposed update:
    ```
    PR update preview:
      Repo:  <WORKSPACE>/<REPO>
      PR:    #<id> — <current-url>

      Title: <new-title>

      <new-description>

    (a) Update PR
    (b) Edit title
    (c) Edit description
    (d) Abort
    ```
17. From the preview, the user can still choose to edit the title or description before submitting, or abort. Selecting (a) triggers the PATCH call; selecting (d) stops with no changes.

### API update

18. The skill sends a `PUT` request to the Bitbucket API with both `title` and `description` fields, even when only one was changed.
19. Both `title` and `description` are always included in the payload — partial updates are not used.

### Result reporting

20. On success (HTTP 200): the skill reports `PR updated: <url>` where the URL links directly to the PR.
21. On HTTP 401: the skill tells the user the token is invalid or expired and instructs them to regenerate it.
22. On HTTP 403: the skill tells the user the token lacks the required `write:pullrequest:bitbucket` scope.
23. On any other error: the skill shows the `"message"` field from the JSON response prefixed with `Error:`.

### Invariants that must not regress

24. Outside of auto mode, the skill never makes an API call without explicit user confirmation at the preview step.
25. Aborting at any step — mode selection or preview — leaves the PR on Bitbucket unchanged.
26. The skill never asks the user to supply a PR number; auto-detection is always used.
27. The existing PR title and description are always shown before the user is asked to provide new values, so the user can make an informed edit.

### Auto mode

28. The skill accepts an `--auto` flag. When passed, the mode selection menu is skipped and the skill proceeds directly to re-derive title and description from commits (equivalent to selecting option (a) in interactive mode).
29. In auto mode, the preview and confirmation step is also skipped — the PR is PATCHed immediately after the draft is produced.
30. Pre-flight checks (invariants 1–3) and PR auto-detection (invariants 4–7) run identically in auto mode.
31. If the commit range is empty in auto mode, the skill stops and reports the error without updating the PR — same as invariant 12.
32. If multiple open PRs are found for the branch in auto mode (invariant 7), the skill stops and reports the ambiguity rather than prompting — the user must resolve it interactively.
33. Result reporting (invariants 20–23) is identical in auto mode.
