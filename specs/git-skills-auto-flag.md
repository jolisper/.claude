# Spec: `--auto` Flag for Git Family Skills

## Summary

Add an `--auto` argument to git skills that skips interactive confirmations by using
Claude's best judgment for defaults, while still stopping on errors and decisions that
genuinely require user intervention.

## Motivation

Some workflows (trust-heavy sessions, quasi-scripted operations) don't need the
per-step confirmation prompts that the git skills currently require. An `--auto` flag
would let users opt into a non-interactive mode without changing the default behavior
for everyone else.

## Contract

- **Auto-safe decisions**: Claude picks the sensible default and proceeds without
  asking. Example: using the AI-generated commit message without confirmation.
- **Must-stop situations**: Errors (auth failures, API errors, network issues) and
  decisions that are genuinely ambiguous or destructive without more context. Example:
  merge/rebase conflict resolution, sensitive data detection.

## Design Options

### Option A — Simple flag (preferred starting point)

`--auto` enables non-interactive mode. Claude uses its best judgment for every
auto-safe decision. No per-decision overrides.

```
/git-commit --auto
/git-new-branch --auto
/git-pr --auto
```

### Option B — Flag + per-decision overrides

`--auto` is a base flag, with optional modifiers for the hard cases that would
otherwise block. More verbose but fully predictable.

```
/git-rebase --auto --on-conflict=ours
/git-pull --auto --on-conflict=theirs
```

Option B is the natural evolution of Option A once conflict-heavy skills are tackled.

## Per-Skill Breakdown

### `git-commit`

| Decision | Auto behavior |
|---|---|
| No staged changes — choose grouping | Stage all changes as one group |
| Confirm proposed commit message | Accept without confirmation |
| Sensitive data detected | **Stop — always requires user confirmation** |

### `git-new-branch`

| Decision | Auto behavior |
|---|---|
| No branch name — choose type | Use `feat` as default type |
| No branch name — choose description | Use first suggested option |
| Dirty working tree — confirm checkout | Proceed (stash if needed) |
| Branch name spec violation | **Stop — fix is ambiguous** |

### `git-pr`

| Decision | Auto behavior |
|---|---|
| Confirm drafted title/description | Submit without confirmation |
| Current branch is main/master/develop | **Stop — shared branch guard** |
| No commits vs base branch | **Stop — nothing to PR** |
| Missing/invalid BITBUCKET_TOKEN | **Stop — auth error** |
| API error | **Stop — surface error to user** |

### `git-push`

| Decision | Auto behavior |
|---|---|
| Upstream not set — confirm `-u` push | Set upstream and push |
| Clean ahead push — confirm | Push without confirmation |
| Divergence detected — force or pull | **Stop — destructive without more context** |
| Auth/network error | **Stop** |

### `git-rebase`

| Decision | Auto behavior |
|---|---|
| Dirty working tree — stash or abort | Stash, rebase, restore |
| Shared branch — confirm history rewrite | **Stop — always requires explicit confirmation** |
| Post-rebase build/test check | Skip (default: no) |
| Conflict resolution per file | **Stop — requires judgment** |

### `git-pull`

| Decision | Auto behavior |
|---|---|
| Dirty working tree — stash/commit/abort | Stash, pull, restore |
| Post-pull build/test check | Skip (default: no) |
| Conflict resolution per file | **Stop — requires judgment** |

### `git-commit-push`

Inherits `--auto` behavior from both `git-commit` and `git-push`. The explicit
"All commits done. Ready to push?" confirmation is skipped. All blockers from
both sub-skills still apply.

## Implementation Notes

- `--auto` should be threaded through composition: skills that call other skills
  (e.g., `git-commit-push`) must propagate the flag.
- Each skill should document in its SKILL.md what `--auto` does and does not skip,
  so users have clear expectations.
- The flag name `--auto` is preferred over `--yes` / `-y` because it conveys
  "use judgment" rather than "accept everything blindly".

## Rollout Order

Start with the three high-value, conflict-free skills where `--auto` automates
nearly everything:

1. `git-commit`
2. `git-new-branch`
3. `git-pr`

Then extend to the conflict-heavy skills once Option B (per-decision overrides)
is designed:

4. `git-push`
5. `git-pull`
6. `git-rebase`
7. `git-commit-push`

## Open Questions

- Should `--auto` imply a specific conflict resolution policy (e.g., always `ours`)
  or remain a hard stop? Leaning toward hard stop until Option B is designed.
- Should `--auto` suppress all output, or just skip prompts? Current leaning: skip
  prompts only, keep output.
- Should skills log which auto decisions were made for traceability?
