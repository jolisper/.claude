# Spec: `tdd-auto` Agent — Autonomous TDD Orchestrator

## Problem Statement

The existing `/tdd` skill (to be renamed `/tdd-cycle`) orchestrates three agents (`tdd-red`, `tdd-green`, `tdd-refactor`) but requires the user to manually provide each behavior to test at every cycle. This creates friction: the user must context-switch between thinking about "what to test next" and reviewing agent output. The agent that should be deciding the next minimal behavior — based on what's already implemented — is the user, and that's the bottleneck.

## Goals & Success Criteria

- The agent autonomously drives full TDD sessions from a problem description to a working implementation
- The user only intervenes at the start (clarification) and optionally during the session (when completion is ambiguous)
- Each behavior passed to `tdd-red` is precise enough that the red agent never needs to interpret or guess
- The implementation emerges through middle-out TDD: starting at the core domain, expanding outward
- For new projects, the agent proposes a simple architecture before the first cycle

## Agent Identity

**File:** `~/.claude/agents/tdd-auto.md`

```yaml
name: tdd-auto
description: >
  Autonomous TDD orchestrator: given a problem description, understands the
  project architecture, finds the middle-out starting point, then drives
  red-green-refactor cycles by determining the next minimal behavior to test
  at each step. Asks clarifying questions upfront, evaluates completion
  dynamically, and stops when the goal is fully implemented.
tools: AskUserQuestion, Agent, Read, Glob, Grep
```

## Workflow

```
User Input (problem description)
  → Phase 1: Architecture Understanding
  → Phase 2: Clarification
  → Phase 3: Dynamic TDD Loop
      → 3a: Derive next behavior (read prior tests + impl)
      → 3b: tdd-red (failing test)
      → 3c: tdd-green (minimal implementation)
      → 3d: tdd-refactor (clean up)
      → 3e: Evaluate completion → loop or stop
  → Phase 4: Final Summary
```

---

## Phase 1 — Architecture Understanding

### Goal

Understand the project structure to determine where the feature lives and where to start the first TDD cycle.

### Branch A: Existing project

1. Scan directory structure (Glob for source dirs, test dirs, config files)
2. Identify the architecture pattern (layered, MVC, hexagonal, modules, flat, etc.)
3. Read related files to understand naming conventions, dependency patterns, existing abstractions
4. Locate the module/package/directory where the new feature belongs
5. Identify the **middle** — the core domain unit that is the heart of the feature

The "middle" is the innermost unit of logic with no infrastructure dependencies: a pure function, a domain class, a core algorithm. Not a controller, not a repository, not a CLI handler.

### Branch B: New project

1. Detect the language/framework from lockfiles, config files, or project markers
2. Propose a **simple, minimal architecture** appropriate for the problem:
   - Name the modules/files that will exist
   - State which is the core domain module (the middle)
   - Keep it flat unless the problem clearly demands layers
   - The architecture must be concrete enough for `tdd-red`/`tdd-green` to follow (e.g., "a `Cart` class in `src/cart.ts` with item operations" — not "a clean architecture with ports and adapters")
3. Present the architecture to the user and **confirm before proceeding**

---

## Phase 2 — Clarification

### Goal

Resolve ambiguities the agent cannot infer from the codebase.

### Rules

- Ask only what is genuinely ambiguous and cannot be detected from the project
- May ask follow-up questions (not limited to a single message)
- Use `AskUserQuestion` for each question
- Focus on:
  - Scope boundaries (what is explicitly out of scope)
  - Acceptance criteria or constraints that affect design (e.g., must be stateless, must persist to disk, must be thread-safe)
  - Behaviors that are already implemented and should be excluded
- Do NOT ask about:
  - Language, framework, test runner — detect from the project
  - List of behaviors — that is the agent's job

### Middle-out confirmation

| Scenario | Action |
|---|---|
| New project | Always confirm proposed architecture + starting point |
| Existing project, middle unclear | Suggest the middle, ask for confirmation |
| Existing project, middle clear | Proceed without asking |

---

## Phase 3 — Dynamic TDD Loop

### State tracked across cycles

| State | Description | Lifetime |
|---|---|---|
| Session context | Problem description + clarifications + architecture decisions | Entire session |
| Accumulated implementation files | All impl files touched so far (deduplicated) | Grows each cycle |
| Cycle history | List of behaviors tested and outcomes | Grows each cycle |

### Each Cycle

#### 3a — Derive Next Behavior

This is the agent's **primary responsibility** and its most critical output.

**Process:**
1. Read the test files and implementation files from all previous cycles
2. Compare what exists against the session context / main goal
3. Determine the **next minimal specific behavior** to test

**Middle-out progression:**
- Cycle 1: core domain unit (the "middle") — the simplest behavior that makes the concept exist
- Subsequent cycles: expand from the middle — add complexity, then edge cases, then error cases
- Save integration with outer layers (persistence, HTTP, CLI) for later cycles

**Behavior description quality rules (non-negotiable):**

The behavior passed to `tdd-red` must satisfy ALL of these:

1. Names the exact function, method, or module under test
2. Specifies exact inputs (concrete values or concrete types)
3. Specifies the exact expected output or side effect
4. Is a single sentence
5. Contains zero ambiguity — the `tdd-red` agent must not need to make any interpretation

**Examples:**

| Quality | Behavior description |
|---|---|
| Bad | "handle empty input" |
| Bad | "the cart should calculate totals" |
| Bad | "add discount support" |
| Good | "`Cart.total()` returns `0` when the cart has no items" |
| Good | "`parse('')` returns an empty list" |
| Good | "`Cart.add(item)` increases `Cart.items.length` by 1 and stores the item with its name and price" |
| Good | "`applyDiscount(100, 0.1)` returns `90` (subtracts 10% from the price)" |

#### 3b — Red Phase

Invoke the `tdd-red` agent via the `Agent` tool with `subagent_type: "tdd-red"`. Pass:
- The session context (problem description + architecture)
- The exact behavior description from 3a

Capture from agent result: test file path, test name, failure output.

#### 3c — Green Phase

Invoke the `tdd-green` agent via the `Agent` tool with `subagent_type: "tdd-green"`. Pass:
- The failing test file path and test name from 3b

Capture from agent result: implementation file(s) created or modified. Add to accumulated implementation files (deduplicate).

#### 3d — Refactor Phase

Invoke the `tdd-refactor` agent via the `Agent` tool with `subagent_type: "tdd-refactor"`. Pass:
- The session context
- All accumulated implementation files from every cycle so far (not just this cycle)

Capture from agent result: what was refactored, or "nothing to refactor".

#### 3e — Cycle Summary

Print after each cycle:

```
✓ Red:      <test name> — failing
✓ Green:    <what was implemented>
✓ Refactor: <what was changed, or "nothing to refactor">
Cycle:      <N>
```

---

## Phase 4 — Completion Evaluation

### After each cycle

Compare implemented behaviors against the main goal:
- Are all core behaviors covered?
- Are relevant edge cases tested?
- Are error paths handled?
- Is anything in the session context still unaddressed?

### Stopping rules

| Condition | Action |
|---|---|
| All behaviors implied by the main goal are implemented and tested | Stop → Phase 5 |
| Can't think of more tests but goal has gaps | Re-read session context, add behaviors |
| After 5+ cycles and completion is unclear | Ask the user via `AskUserQuestion` |
| A new requirement emerges outside original scope | Ask the user before adding it |
| Unsure if an edge case is in scope | Ask the user |

### What NOT to do

- Do not stop just because the planned backlog ran out — re-read the session context
- Do not add behaviors beyond the agreed scope without asking
- Do not keep looping indefinitely if the goal is clearly met

---

## Phase 5 — Final Summary

When the goal is achieved, print:

```
## TDD Session Complete — <problem description>

Behaviors implemented (<N> cycles):
1. <exact behavior> → <test name>
2. <exact behavior> → <test name>
...

Implementation files:
- <file path>
- <file path>
...

Architecture: <1-2 sentences on the design that emerged>
```

---

## Key Design Decisions

### Why middle-out?

Starting from the core domain unit means:
- The first tests are pure logic — no mocks, no infrastructure, fast feedback
- The architecture emerges from the domain, not the other way around
- Edge cases are discovered naturally as the core solidifies
- Integration with outer layers is deferred until the core is stable

### Why dynamic backlog instead of upfront planning?

- More aligned with TDD philosophy: you discover what to test next by looking at what you just built
- Avoids over-planning behaviors that become irrelevant as the design emerges
- Each behavior is informed by the actual code, not a guess

### Why strict behavior descriptions?

The `tdd-red` agent writes one test from one sentence. Any ambiguity means it guesses, and a guessed test may not align with the intended design. Precision here prevents cascading misalignment across the entire session.

---

## `/tdd-session` Skill — Entry Point

The agent needs a user-invokable skill as its entry point. This skill is a thin wrapper: it captures the problem description and launches the `tdd-auto` agent.

**File:** `~/.claude/skills/tdd-session/SKILL.md`

```yaml
name: tdd-session
description: >
  Launch an autonomous TDD session. Accepts a problem description, then
  hands off to the tdd-auto agent which drives the full red-green-refactor
  loop without further user input (unless clarification is needed).
disable-model-invocation: true
argument-hint: "<problem description>"
```

### Skill body behavior

1. Capture `$ARGUMENTS` as the problem description
2. If `$ARGUMENTS` is empty, ask the user: "What are you building? Give a brief description of the problem to solve."
3. Launch the `tdd-auto` agent via the `Agent` tool with `subagent_type: "tdd-auto"`, passing the problem description
4. When the agent completes, relay the final summary to the user

The skill does NOT:
- Ask for behaviors (the agent does that autonomously)
- Run any TDD phases itself (fully delegated to the agent)
- Add any context beyond the problem description (the agent scans the project itself)

---

## Rename: `/tdd` → `/tdd-cycle`

The existing `/tdd` skill is renamed to `/tdd-cycle` to clarify the two modes:

| Skill | Mode | Who decides next behavior |
|---|---|---|
| `/tdd-cycle` | Manual | The user provides each behavior |
| `/tdd-session` | Autonomous | The `tdd-auto` agent derives each behavior |

**Change:** Rename `~/.claude/skills/tdd/` to `~/.claude/skills/tdd-cycle/` and update the frontmatter `name` field from `tdd` to `tdd-cycle`. No other changes to the skill body — it works the same, just under a new name.

---

## Dependencies

| Dependency | Purpose |
|---|---|
| `tdd-red` agent | Red phase — writes one failing test |
| `tdd-green` agent | Green phase — minimal implementation to pass |
| `tdd-refactor` agent | Refactor phase — clean up without new behavior |
| `tdd-auto` agent | Orchestrates the loop autonomously |
| `/tdd-session` skill | User-invokable entry point (autonomous) |
| `/tdd-cycle` skill | User-invokable entry point (manual, renamed from `/tdd`) |
| `AskUserQuestion` tool | Clarification, middle confirmation, completion checks |
| `Agent` tool | Spawning the three sub-agents |
| `Read`, `Glob`, `Grep` tools | Architecture understanding, reading prior cycle output |
