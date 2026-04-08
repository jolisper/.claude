---
name: tdd-cycle
description: >
  Run a TDD red-green-refactor loop. Accepts an initial problem description,
  then asks the user for each behavior to test one at a time. Drives the red
  (failing test), green (minimal implementation), and refactor phases using
  dedicated agents. Type 'done' to stop the loop.
disable-model-invocation: true
argument-hint: "<problem description>"
---

# TDD Red-Green-Refactor

Run a red → green → refactor loop, one behavior at a time.

## Setup

The user invokes this skill with an initial problem description (e.g. `/tdd-cycle build a shopping cart`). Capture this as the **session context** — it describes what is being built. Every agent invocation in this session receives this context so agents understand the broader goal.

Resolve `$ARGUMENTS` to the session context:

- If `$ARGUMENTS` is empty, ask for a description before proceeding:
  > What are you building? Give a brief description of the problem to solve.
- If `$ARGUMENTS` looks like a file path (contains `/` or `.` with a known extension such as `.md`, `.txt`, `.spec`, `.feature`, or similar), use the `Read` tool to read it. Use the file contents as the session context. If the file does not exist, tell the user and ask for a description instead.
- Otherwise, use `$ARGUMENTS` as the session context directly.

## Loop

Repeat until the user types "done":

### Ask

Ask the user exactly this:

> What behavior do you want to test next? (type **done** to finish)

Wait for the response before proceeding.

### Red phase

Use the `tdd-red` agent. Pass:
- The session context (problem description)
- The behavior description the user just gave

Wait for the agent to complete.

The agent will return: the test file path, the test name, and confirmation it is failing. Capture this.

### Green phase

Use the `tdd-green` agent. Pass only:
- The failing test file path and test name from the red phase

Wait for the agent to complete. The agent will return: the implementation file(s) changed and confirmation tests are passing. Add the returned files to the **accumulated implementation files** list (tracked across all cycles in this session).

### Refactor phase

Use the `tdd-refactor` agent. Pass:
- The session context (problem description)
- All accumulated implementation files from every cycle so far (not just this cycle)

Wait for the agent to complete.

### Cycle summary

After all three phases, report to the user:

```
✓ Red:     <test name> — failing
✓ Green:   <what was implemented>
✓ Refactor: <what was changed, or "nothing to refactor">
```

Then return to **Ask** for the next behavior.

## Stopping

When the user types "done", print a final summary of all behaviors tested in this session and stop.
