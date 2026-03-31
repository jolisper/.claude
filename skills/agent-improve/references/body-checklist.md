# Agent Body Checklist

Check against `references/best-practices.md` for detailed guidance on each item.

## HIGH findings

- A tool is instructed in the body but missing from `tools` (runtime failure)

## MEDIUM findings

- Instructions are declarative ("the agent should…") not procedural ("run…, read…, then…")
- No intake/discovery section — agent reasons without first establishing the ground truth
- No escalation conditions defined (when should the agent stop and ask the user?)
- Body is a character description with no behavioral procedures
- Verbatim quotations or large static reference blocks embedded inline (always loaded, cannot be deferred)
- Rationalization resistance absent: discipline-enforcing rules lack counter-rationalizations for likely skip scenarios (e.g. "the change looks trivial", "we're almost done")
- Failure contract incomplete: body describes only the happy path — no error output format, no recovery steps, no subprocess failure handling
- Exclusion conditions missing: no explicit "when NOT to use" or "abort if" conditions for destructive or context-sensitive operations
- Delegation transparency gap: agent delegates to sub-agents or subprocesses but does not restate tool restrictions and behavioral contracts at the delegation boundary
- Cluster consistency violation: agent shares logic with sibling agents (e.g. error formatting, confirmation gates) but uses a different implementation — creates maintenance risk

## LOW findings

- Output format not specified (agent outputs vary across invocations)
- Body exceeds ~300 lines (heavy system prompt; review for deferrable content)
- Persona section is purely declarative and adds no behavioral guidance
