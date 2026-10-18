---
name: spec-partition
description: >
  Split a large functional-spec.md into an ordered chain of smaller, independently
  implementable functional specs, without adding, removing or rewording any invariant.
  Requires a functional-spec.md written by spec-functional.
disable-model-invocation: true
argument-hint: "<initiative-name>"
allowed-tools: Read Glob Write Bash(git rev-parse:*) Bash(python3:*)
when_to_use: >
  Invoke after spec-functional and before spec-technical, when a spec has more than ~30
  invariants or mixes concerns that share no state, error codes or fixtures. Stops if no
  functional-spec.md exists or no clean cut into parts of 8+ invariants exists.
effort: high
---

Divide one big `functional-spec.md` into N smaller functional specs. Each new spec is a
sibling initiative that `spec-technical` and `spec-implement` can consume unchanged. The
specs form an ordered chain: spec K may assume specs 1..K-1 are already implemented, and
may never depend on spec K+1 or later.

Judgment lives in two JSON files you write: the dependency graph (Step 3) and the prose
selection (Step 7). Everything else (clustering, ordering, renumbering, reference
rewriting, file writing, verification) is done by scripts. Do not redo their work by hand
or edit their output files; change the inputs and rerun.

## Available scripts

All in `~/.claude/skills/spec-partition/scripts/`, run with `python3`. Each prints
`status=…` first, then key=value lines; `--help` documents flags and JSON formats.

- `plan-partition.py --original <spec> --graph <graph.json> --out <plan.json> [--join A:B] [--move A:B]`
  clusters, merges cycles, lists cycle-break candidates, merges small parts, orders parts,
  and decides `split` / `no-split`.
- `write-partition.py --original <spec> --plan <plan.json> --prose <prose.json> [--overwrite]`
  writes every part's `functional-spec.md` and `initiative.md` plus `partition.md`.
  Behavior items are copied byte for byte and their references rewritten.
- `verify-partition.py --original <spec> [--part <dir> ...] [--plan <plan.json>]`
  counts invariants (no `--part`) or verifies a written partition.

Working files live in `<root>/initiatives/<name>/.partition/` (`graph.json`, `plan.json`,
`prose.json`). They are the only files written before approval.

## Hard rule: reorganize only

This skill never creates, deletes, merges, splits, rewords, strengthens or weakens an
invariant. Output invariants are exactly the input invariants, partitioned. The only
permitted edit to invariant text is replacing a cross-reference number token, and
`write-partition.py` does that. Any other change is a defect.

Even when an invariant reads awkwardly out of its original context, or a small rewording
would make a part "cleaner", leave it alone. Fixing wording is spec-functional's job, not
this skill's.

An invariant that bundles several claims stays whole and lands in one part. If a cycle or
size problem seems to require splitting it, do not split it: report it in Step 6 as a
"compound invariant blocking the partition" and let the user decide (for example by editing
the original spec and re-running).

## When not to use

- No clean cut exists: the plan decides `no-split` (Step 4 stops).
- The initiative is already being implemented (`initiatives/<name>/logbook.md` exists):
  partitioning renumbers the invariants that the logbook and tests cite. Step 1 gates this.
- The user wants invariants reworded or split: send them to `/spec-functional` instead.

## Failure contract

Any script printing `status=error`: report its `message` and `hint` lines verbatim and
stop. Do not work around a script by doing its step by hand.

## Steps

**Step 1: Resolve root, locate the spec, check for implementation**

Run `git rev-parse --show-toplevel` (fall back to the cwd and say so). `$ARGUMENTS` is the
initiative name; if empty, ask:

    Which initiative do you want to partition?
    Enter the initiative name (directory name under initiatives/):

Read `<root>/initiatives/<name>/functional-spec.md`. If missing, stop:

    No functional-spec.md found at initiatives/<name>/functional-spec.md.
    Write it with /spec-functional first.

Glob `<root>/initiatives/<name>/logbook.md`. If it exists, ask:

    initiatives/<name>/logbook.md exists: implementation has started. Partitioning
    renumbers invariants the logbook and tests cite. How do you want to proceed?
    (a) Proceed
    (b) Cancel

If `initiatives/<name>/technical-spec.md` exists, note that it will describe the
unpartitioned spec and go stale; do not touch it.

**Step 2: Count**

Run `verify-partition.py --original <root>/initiatives/<name>/functional-spec.md`. Use
`invariants=<N>`; do not count by hand. If N < 16, report "<N> invariants: no split
needed" and stop (two parts of 8 cannot exist).

**Step 3: Write the dependency graph**

Treat each numbered invariant as a node. Record an edge for each pair where any of these
holds, with the evidence (the shared term, code or state):

| rule | holds when |
|---|---|
| `ref` | one invariant names the other's behavior (numeric "invariant N" citations are added automatically) |
| `code` | both share an error code (set `codes` to how many) |
| `order` | both sit in the same ordering or precedence rule |
| `state` | both read or write the same named file, store, session, connection or data structure |
| `output` | one describes a value another consumes ("as returned by X") |
| `fixture` | one cannot be observed or tested without the preconditions the other establishes |

`from` is the dependent and `to` its prerequisite. Set `"directed": false` when direction
is unclear. Direction decides clustering: undirected strong edges (typically `state`,
`order`, shared `code`s) keep invariants in one part, while directed edges (B needs A)
only order parts and may cross them, pointing backward, which becomes Assumes. Mark an
edge directed only when one side clearly builds on the other and not the reverse; marking
a mutual coupling directed both ways just produces a cycle merge. Do not infer an edge
from topic similarity alone. If you cannot name the
shared term, code or state, there is no edge. Behavior sub-section headings are hints,
not edges.

Also list cross-cutting invariants (isolation, read-only, concurrency, networking limits)
in `crosscutting`. They land wherever their edges put them, and every later part gets a
"Must not regress" citation of them.

Write `.partition/graph.json`:

    {"edges": [{"from": 12, "to": 3, "rules": ["code"], "evidence": "E_EMPTY"}],
     "crosscutting": [5]}

**Step 4: Plan**

Run `plan-partition.py --original <spec> --graph <root>/initiatives/<name>/.partition/graph.json --out <root>/initiatives/<name>/.partition/plan.json`.

On `decision=no-split`, report "<N> invariants: no split needed (<reason>)" and stop.
`reason=no_clean_cut` means 40 or fewer invariants without two or more cohesive groups of
8+ (groups held together by undirected edges, after merging cycles). If the output has
any `cycle_merge` line, show it and its candidates as in Step 6 before stopping, so the
user can opt to rerun with a `--move`.

**Step 5: Name the parts**

Give each planned part a short kebab-case slug naming its concern, and a one-line scope.
This is the only per-part judgment before approval.

**Step 6: Present the partition and ask for approval**

Show, from the script's output (do not recompute):

- A table: part number, slug, invariant count, assumes, flags, one-line scope.
- Per part, the old invariant numbers it receives.
- Every `cross_edge` and `weak_kept_apart` line with its evidence.
- Every `cycle_merge` and its `cycle_break_candidate` lines (each is a ready `--move`).
- `oversized`, `independent` or `small_unmerged` flags, and any compound invariant
  blocking the partition.

Then ask:

    How do you want to proceed?
    (a) Approve and write the specs
    (b) Adjust (name the moves or merges)
    (c) Cancel

On (b): translate the request into `--join A:B` (same part as B) or `--move A:B` (A alone
into B's part), rerun Step 4 with all flags so far, and repeat Steps 5–6. If the user's
edges are wrong rather than the clustering, fix `graph.json` instead. On (c): stop;
leave `.partition/` for a later rerun.

**Step 7: Write the specs**

Write `.partition/prose.json`, one entry per part in chain order:

    {"parts": [{"slug": "core", "scope": "<sentences copied from initiative.md>",
                "sections": {"Summary": "<sentences copied from the original>",
                             "Non-goals": "- Sync.\nCovered by <name>-02-export."}}]}

Section names are the original's non-Behavior section titles (Summary, Problem, Goals /
Non-goals, Design, Open questions). Copy only original sentences that apply to the part,
without rewording or adding any. Omit a section that has none. The only addition allowed
is a one-line neighbor pointer "Covered by <part-dir>." Copy each dedicated Open
questions entry into the part holding the invariants it concerns. If the original has no
initiative.md, copy `scope` from its Summary.

Run `write-partition.py --original <spec> --plan <plan.json> --prose <prose.json>`.

- `status=exists`: list the `path=` lines and ask
  `(a) Overwrite them / (b) Cancel`. On (a), rerun with `--overwrite`.
- `status=fail`: nothing was written. Report each `later_ref`, `mixed_ref`, `range_ref`
  or `bad_ref` line (the original invariant and token). Offer `(b) Adjust` from Step 6 or
  cancel. A `range_ref` or `mixed_ref` usually needs the original spec edited with
  /spec-functional.
- `status=error` after a partial write: the `written=` lines list what landed. Output is
  regenerated from the plan, so fix the cause and rerun with `--overwrite`.

The script never modifies the original functional-spec.md.

**Step 8: Verify before reporting**

Run the verifier, even though the files came from a script: it is an independent check
against the original, and it is the only check on the prose you selected.

    python3 ~/.claude/skills/spec-partition/scripts/verify-partition.py --original <spec> --plan <plan.json> --part <root>/initiatives/<part-1-dir> --part <root>/initiatives/<part-2-dir>

Pass every part in chain order. On `status=fail`, report every problem line as-is. Fix
only by correcting `prose.json` (for `prose_added`) or the plan inputs, then rerun Step 7
with `--overwrite` and this step. Never edit a part file by hand to make it pass.

On `status=pass`, output:

    Partitioned <name> into <N> specs (see initiatives/<name>/partition.md).
    Next: /spec-technical <first-part-dir>, then implement in order.

## Writing guidance

- Verbatim over rewording: a partition changes where invariants live, never what they say.
- Prefer fewer, larger parts over many tiny ones; a part exists to be implementable on its
  own, not to be small.
- Each part must be testable by itself once its prerequisites exist.
