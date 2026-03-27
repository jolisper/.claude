# Skill Body — Best Practices

Source: https://agentskills.io/docs/best-practices
Fetch that URL for full details when in doubt.

## Write procedures, not descriptions

**Do:** "Run `git status`. If untracked files exist, ask the user which to stage."
**Don't:** "The skill should check for untracked files."

Instructions should tell the agent *what to do*, not *what the output should look like*.

## Match prescriptiveness to reversibility

- **Destructive / irreversible actions** (deletes, overwrites, pushes): be explicit and stepwise. Include confirmation gates.
- **Reversible / low-risk actions** (reads, searches, analysis): be flexible. Let the agent use judgment.

## Confirmation gates

Before any destructive action, show the user what will happen and ask for explicit approval. Use a lettered menu:

```
About to delete <X>. How do you want to proceed?
(a) Proceed
(b) Cancel
```

Never auto-proceed on destructive actions unless the skill's purpose is explicitly to automate them.

## Provide defaults, not menus

Bad: "You can use approach A, B, or C depending on the situation."
Good: "Use approach A. If A isn't applicable because of X, fall back to B."

Give the agent a decision, not a list of options to choose from.

## Use validation loops

For multi-step workflows that can fail:

```
1. Do X
2. Validate: check Y
3. If Y fails, fix Z and repeat from step 1
4. Continue only when Y passes
```

## Output templates

Include an inline template when format consistency matters across invocations:

```
Present findings as:

[SEVERITY] Rule N — Rule Name
  Location: <method or line>
  Problem: <observable fact>
```

Omit templates when the output format is flexible or context-dependent.

## Progressive disclosure

Skills load in three tiers. Design your skill so each tier is as small as possible:

| Tier | What's loaded | When | Token cost |
|---|---|---|---|
| 1. Catalog | Name + description only | Session start | ~50–100 tokens per skill |
| 2. Instructions | Full `SKILL.md` body | When the skill is activated | <5000 tokens recommended |
| 3. Resources | Reference files, scripts, assets | When instructions reference them | Varies |

The model sees tier 1 from the start. It loads tier 2 when it decides the skill is relevant. Tier 3 files are loaded individually, on demand, as the body instructs.

**Consequence for authoring:** keep tier 2 (the body) lean. Bloated `SKILL.md` files are expensive every time the skill activates and are more likely to be pruned by the client's context compaction logic — silently degrading the agent's behavior mid-conversation without any visible error.

## Size and modularity

- Keep `SKILL.md` under 500 lines (tier 2 budget)
- Move reference material (rule tables, API docs, agent conventions) to `references/*.md` (tier 3)
- In `SKILL.md`, tell the agent *when* to read each reference file:
  - "Before drafting the message, read `references/conventions.md`."
  - "If the user mentions X, read `references/edge-cases.md`."
- Name reference files explicitly in the body — some clients surface available resources to the model at activation time, but the body's read instructions are the reliable trigger

## Add what the agent lacks

Don't document things the agent already knows (how to use git, how to write JSON, common patterns). Only add:
- Domain-specific rules the agent wouldn't know (e.g. your team's commit format)
- Workflow sequencing that isn't obvious
- Project-specific context
- Edge case handling the agent gets wrong without guidance

## $ARGUMENTS

Use `$ARGUMENTS` to reference user-supplied input when the skill accepts a parameter. Check for empty `$ARGUMENTS` at the start and ask for input if needed.

---

## Robustness patterns

See `references/robustness-patterns-rationale.md` for the origin and reasoning behind these patterns.

### Rationalization resistance

For any rule that a model might skip under pressure ("it seems simple enough", "we're almost done"), include an explicit counter-rationalization in the skill body.

**Do:** "Run the full test suite before marking done — even when the change looks trivial."
**Don't:** "Run tests before marking done."

Add a note for the most likely skip scenario: "Even if only one line changed, still run tests — single-line changes have caused regressions before."

### Failure contract completeness

Specify what happens when the skill fails, what the output format is, and what the recovery path is. Do not describe only the happy path.

**Do:** Include a section: "If X fails: report the error to the user, explain what to check, and stop — do not proceed to the next step."
**Don't:** Describe only the successful workflow and leave failure handling implicit.

This is especially important when the skill delegates to a subprocess or subagent — document what happens if that subprocess fails.

### Exclusion conditions

Include an explicit "when NOT to use this skill" or "abort if" section, especially for destructive or context-sensitive operations.

**Do:** "Abort and warn the user if the current branch appears to be a shared or protected branch."
**Don't:** Assume the user will only invoke the skill in safe contexts.

Gate on context the skill can check (branch name, dirty working tree, missing upstream) and surface the risk before acting.

### Delegation transparency

When a skill delegates to another skill or subprocess at runtime, explicitly restate the tool restrictions and behavioral contracts at the delegation boundary.

**Do:** "Launch a subagent with `allowed-tools: Read Grep` — do not pass Write or Bash."
**Don't:** Rely on tool restrictions being silently inherited from a runtime-read SKILL.md.

If the delegating skill has a blank `allowed-tools`, note explicitly why and what the effective tool surface is during execution.

### Cluster consistency

If this skill shares logic with one or more sibling skills (e.g., conflict resolution, error formatting, confirmation gate patterns), use the same implementation — same script, same steps, same wording.

**Do:** "Use the same `resolve-conflict.py` script used in `git-pull`."
**Don't:** Re-implement the same logic inline with slight variations.

Divergence between sibling skills creates maintenance risk and inconsistent user experience. If you find shared logic, extract it to a script or reference file so both skills use the same source.
