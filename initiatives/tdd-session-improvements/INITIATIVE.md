# Initiative: tdd-session improvements

## Summary

Two targeted improvements to the `tdd-session` skill: a baseline health check before the loop starts, and a checklist-based completion criterion to replace subjective assessment.

## Origin

Triggered by reading [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) (Anthropic Engineering). The article's core thesis — that harnesses must manage continuity across context windows — was used as a lens to audit `tdd-session`.

Most article patterns already exist or were intentionally rejected:

- Logbook in `tdd/sessions/` already handles per-session records.
- Sub-agent isolation (each agent receives only what it needs) is intentional and correct — not a gap.
- Resume from prior sessions was rejected: sessions are independent by design, and not all project changes go through `tdd-session`, so a session log cannot represent full code state.

Two real gaps surfaced.

## Changes

### 1 — Baseline health check

**File:** `skills/tdd-session/SKILL.md`
**Location:** New section after `## Setup`, before `## Step 1 — Find the Middle`.

Run the test suite before starting. If any tests fail, report them and stop. A TDD session must start from green — starting from red makes it impossible to distinguish a new failure from a pre-existing one. If no tests exist yet, proceed normally.

One Bash call. Hard stop on failure. No AskUserQuestion.

### 2 — Checklist-based completion

**File:** `skills/tdd-session/SKILL.md`

#### 2a — Behavior checklist at session start
**Location:** Step 2 — Start the Logbook, after the opening paragraph.

Derive a numbered checklist of behaviors from the problem description and write it to the logbook. Each item follows the Step 3a format: function/method, exact inputs, exact expected output, single sentence. This checklist is the definition of done for the session.

#### 2b — Coverage check instead of subjective assessment
**Location:** Step 3e — Log and evaluate, replacing the "assess whether the goal is fully implemented" line.

After each cycle, cross-check each checklist item against passing tests. An item is covered when a green test exercises it. The session ends when every item is covered and the full test suite passes. At the cycle limit (10), stop and report which items are covered and which are not — no AskUserQuestion.

## Design principles preserved

- Sub-agents remain isolated: no global context injected into tdd-red, tdd-green, or tdd-refactor.
- Sessions remain independent: no resume from prior sessions.
- The orchestrator never writes code: only the logbook.
- The session is fully autonomous: no user prompts during the loop.

## Status

- [x] Initiative documented
- [ ] Changes implemented in `skills/tdd-session/SKILL.md`
- [ ] Changes validated against a real tdd-session run
