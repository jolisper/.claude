# Robustness Patterns — Origin and Rationale

## Background

These five patterns were extracted from a quality gap analysis comparing the skills in this collection against three community skill repositories:

- **obra/superpowers** — battle-tested development workflow skills with strong behavioral enforcement
- **anthropics/skills** — the official Anthropic skill collection; polished, document/media focused
- **Trail of Bits claude-skills** — security-focused skills with deep static analysis tooling

The analysis identified recurring structural weaknesses in the local skills. Rather than fixing each skill individually, the patterns were generalized and added here so that `skill-create` and `skill-improve` automatically check for them going forward.

## Per-pattern origin

### Rationalization resistance
**Source:** obra/superpowers

obra skills use "Iron Law" blocks, rationalization tables, and common-excuse counters — engineering the skill to resist the model's own tendency to rationalize shortcuts under pressure. Skills like `systematic-debugging` and `verification-before-completion` explicitly counter scenarios like "the change seems small" or "we're almost done."

**Local weakness addressed:** `refactor` had a confirmation gate but no counter-rationalization. Nothing in the body prevented the model from skipping the confirmation by treating the task as obviously safe.

### Failure contract completeness
**Source:** obra/superpowers; Trail of Bits

obra skills for subagent orchestration (`dispatching-parallel-agents`, `subagent-driven-development`) specify subprocess failure contracts explicitly. Trail of Bits' `differential-review` includes a full error output format and recovery path.

**Local weakness addressed:** `try` (the sandboxed worktree investigation skill) had only 2 lines of body — no failure handling, no output format, no recovery path. `sdk` said "report error and stop" without specifying what the error message should look like or what the user should do next.

### Exclusion conditions
**Source:** Trail of Bits; obra/superpowers

Trail of Bits skills consistently include "do not use on" and "abort if" conditions. obra's `finishing-a-development-branch` checks whether the branch is shared before proceeding.

**Local weakness addressed:** `git-rebase` did not warn about rebasing shared/public branches. `git-push` described `--force-with-lease` as "safe" without gating on whether the branch was shared. Neither skill had a "when NOT to use" section.

### Delegation transparency
**Source:** Structural analysis of local skills

`git-commit-push` had a blank `allowed-tools` and delegated via runtime `Read` calls to `git-commit/SKILL.md` and `git-push/SKILL.md`. This created a gap: the harness couldn't enforce tool restrictions before the first Read, and the effective tool surface during execution was undocumented.

**Local weakness addressed:** `git-commit-push` specifically. Also generalizes to any future skill that orchestrates other skills by reading their SKILL.md at runtime.

### Cluster consistency
**Source:** Structural analysis of local skills

`git-pull` used an inline `python3 -c "..."` one-liner for conflict resolution. `git-rebase` solved the same problem with a proper `resolve-conflict.py` script. The two skills shared nearly identical conflict resolution logic but used different implementations — a maintenance and reliability risk.

**Local weakness addressed:** The `git-pull` / `git-rebase` conflict resolution inconsistency. The pattern generalizes to any skill cluster that shares logic (confirmation gate format, error output structure, branch safety checks).
