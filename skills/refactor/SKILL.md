---
name: refactor
description: Refactor code following the 9 Object Calisthenics rules by Jeff Bay — one level of indentation, no else, wrap primitives, first-class collections, one dot per line, no abbreviations, small entities, max two instance variables, no getters/setters
disable-model-invocation: true
argument-hint: "[file path] or paste code directly"
allowed-tools: Read Edit Glob Grep
---

Refactor code following the 9 Object Calisthenics rules. If you need the full explanation or examples for any rule, read `rules.md`.

## Input

Determine what to refactor from the available context, in priority order:

1. **Pasted code in the message** — if the user pasted a code snippet, refactor that. Use `$ARGUMENTS` as additional focus instructions.
2. **`$ARGUMENTS` with a file path** — read the specified file (and optionally a line range, e.g. `src/Order.java:10-80`) and refactor the relevant section.
3. **Nothing provided** — ask: "What would you like to refactor? Paste the code here or give me a file path (with optional line range)."

## Step 1 — Read and understand the target

- If working from a file path: use Read to load the file. If a line range is specified, focus on that range but read the full file for context.
- If working from pasted code: you already have the code — do not re-read unless you need surrounding context from the file.
- Identify the language. Note any language-specific constraints (e.g. Rule 3 is most strict in statically-typed languages; Rule 5 applies differently to fluent APIs in some languages).

## Step 2 — Analyze violations

Check the code against **every rule** in the quick reference table. Do not skip rules because they seem minor — report every violation found, no matter how small.

For every violation found, record:

- **Which rule** is violated (number and name)
- **Where** exactly (method name, line, or snippet)
- **What** is wrong — stated as observable fact, not opinion
- **Severity** — how much does this violation harm readability, cohesion, or encapsulation?

Present **all** findings as a prioritized list before proposing any changes. Severity is for ordering only — never omit a violation because it is LOW:

```
Violations found:

[HIGH] Rule 1 — One level of indentation per method
  Method: processOrder() — contains nested for + if (2 levels deep)

[HIGH] Rule 9 — No getters/setters
  Methods: getAmount(), getCurrency() expose internal state

[MEDIUM] Rule 2 — No else
  Method: validate() — uses else branch, could use guard clause

[LOW] Rule 6 — No abbreviations
  Variable: mgr → should be manager
```

Severity guide:
- **HIGH**: directly violates encapsulation, cohesion, or single responsibility — includes Rule 10 (bare `new` with type codes or flags leaks construction knowledge to callers)
- **MEDIUM**: increases complexity or duplication
- **LOW**: naming or style concern

If no violations are found, say so explicitly and explain why the code already conforms.

## Step 3 — Confirm scope

After presenting violations, ask the user:

```
Found N violation(s). How do you want to proceed?
(a) Fix all violations
(b) Fix HIGH severity only
(c) Fix specific rules — tell me which ones
(d) Show me the refactored version first, then decide
(e) Cancel
```

Wait for the user's response before proceeding.

## Step 4 — Propose the refactored code

For the agreed scope, show the full refactored version in a fenced code block. Annotate each change with the rule it addresses:

```java
// Rule 1: extracted nested loop into collectRows()
void collectRows(StringBuffer buf) { ... }
```

If a rule would require structural changes beyond the selected snippet (e.g. Rule 3 requires creating a new wrapper class, or Rule 8 requires splitting a class), describe what the full change would entail and ask whether to proceed with the broader refactoring or limit changes to what's within scope.

Then ask:

```
(a) Apply these changes
(b) Adjust something — tell me what
(c) Cancel
```

## Step 5 — Apply

If the user confirms, apply the changes using Edit. Make only the changes discussed — do not refactor beyond the agreed scope.

**Before applying**: strip all rule annotation comments from the code (e.g. `// Rule 1: ...`, `// Rule 8: ...`). These are for the review conversation only — they must not appear in the committed code.

After applying, summarize what was changed and which rules are now satisfied.

## Rules quick reference

| # | Rule | Key constraint |
|---|---|---|
| 1 | One level of indentation per method | Extract nested logic into methods |
| 2 | No else keyword | Guard clauses, polymorphism, Null Object |
| 3 | Wrap all primitives and Strings | `Hour` not `int`, `Email` not `String` |
| 4 | First class collections | A class with a collection has no other fields |
| 5 | One dot per line | Law of Demeter — tell, don't navigate |
| 6 | No abbreviations | Full words, 1–2 word names, no context duplication |
| 7 | Keep all entities small | Max 50 lines per class, 10 files per package |
| 8 | No more than two instance variables | Decompose into collaborating objects |
| 9 | No getters/setters/properties | Tell, don't ask |
| 10 | Replace Constructor with Factory Method | `new Foo("E")` → `Foo.createEngineer()` |
| 11 | Decompose Conditional | Extract condition + branches into named methods |
| 12 | Consolidate Conditional Expression | Combine checks with same result into one named method |

If you need the full explanation or examples for a specific rule, read `rules.md`.
