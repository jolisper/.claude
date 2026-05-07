# Spec Template

Read this file in Step 4 before drafting. Fill every section; leave no placeholders.

---

## Format

~~~markdown
# Spec: <Title>

## Overview
<2–4 sentences: what this module does, why it exists, key design decisions.
Written for a developer who has never seen the project. Mention the language,
runtime, and where the module lives.>

## Goal
<One sentence. What the complete implementation achieves from the caller's
perspective. Start with a verb: "Provide…", "Implement…", "Expose…">

## Technology
- Language: <language + version if relevant>
- Test runner: <e.g. Jest, pytest, go test, ExUnit>
- Entry module: <file path or package name where the new code lives>
- Dependencies: <any libraries this may use, or "none beyond stdlib">

## Behaviors
Ordered from simplest to most complex. Each behavior is a single unambiguous
sentence that names the exact function, exact inputs, and exact expected output
or side effect. tdd-session passes each line directly to tdd-red.

Format: `function(inputs) → output` — optional clarification

1. `function(inputs) → output` — description
2. ...

## Constraints
Technical or design rules the implementation must honor — even when not
directly tested.

- <constraint>

## Out of scope
Explicit list of things that must NOT be built. At least one entry required.

- <item>

## Acceptance criteria
Higher-level checks confirming the goal is fully met, verified after all
behaviors pass.

- [ ] <criterion>
~~~

---

## Behaviors section — guidance

This is the most critical section. Weak behaviors produce weak tests.

**What makes a good behavior:**
- Concrete: `add(2, 3) → 5`, not `add two numbers`
- Testable: maps to a single assertion, not a paragraph
- Ordered: simplest first so tdd-session builds up incrementally

**Coverage checklist before finalizing:**
- [ ] One behavior per happy-path variant
- [ ] One behavior per meaningful edge case (empty, zero, boundary)
- [ ] One behavior per expected error or rejection (invalid type, out of range)
- [ ] One behavior per side effect (mutation, IO, event) if applicable

**Anti-patterns to avoid:**
- Vague: `handles errors gracefully` → rewrite as `parse("") throws ParseError`
- Compound: `accepts strings and numbers` → split into two behaviors
- Implementation detail: `calls validator before saving` → rewrite as an observable output

---

## Example

~~~markdown
# Spec: Password Strength Checker

## Overview
A pure function that scores a candidate password 0–4 based on length, character
variety, and common-password rejection. Lives in `src/auth/password-strength.ts`.
No I/O, no state.

## Goal
Expose a `checkStrength(password: string): number` function that returns an integer
score the registration form uses to gate sign-ups.

## Technology
- Language: TypeScript
- Test runner: Vitest
- Entry module: src/auth/password-strength.ts
- Dependencies: none beyond stdlib

## Behaviors
1. `checkStrength("ab")` returns `0` — fewer than 8 chars scores 0
2. `checkStrength("abcdefgh")` returns `1` — 8+ chars, lowercase only
3. `checkStrength("Abcdefgh")` returns `2` — adds uppercase
4. `checkStrength("Abcdefg1")` returns `3` — adds digit
5. `checkStrength("Abcdefg1!")` returns `4` — adds symbol, full score
6. `checkStrength("password")` returns `0` — common password, capped at 0
7. `checkStrength("")` returns `0` — empty string
8. `checkStrength(null)` throws `TypeError` — non-string input rejected

## Constraints
- Pure function: no side effects, no I/O, no global state
- Common-password check is case-insensitive
- Score must be an integer 0–4 inclusive

## Out of scope
- Async validation
- External dictionary lookups
- UI rendering

## Acceptance criteria
- [ ] Score 0 blocks form submission; score 4 enables it
- [ ] All 8 behaviors pass with no test skips
- [ ] Function is exported as a named export from the entry module
~~~
