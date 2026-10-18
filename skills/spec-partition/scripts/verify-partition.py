#!/usr/bin/env python3
"""Mechanical checks for spec-partition.

Count mode (no --part):
  verify-partition.py --original <functional-spec.md>
  -> status=count invariants=<N>

Verify mode:
  verify-partition.py --original <functional-spec.md> --part <dir-or-file> [--part ...]
                      [--plan <plan.json>] [--expect-counts 12,9,15]
  Parts are given in chain order (part 1 first). A directory means <dir>/functional-spec.md.

Checks:
  missing / extra   every original invariant appears in exactly one part (multiset
                    equality after masking cross-reference tokens, whitespace collapsed)
  count             per-part counts match --expect-counts (or the plan)
  numbering         each part's Behavior list is numbered 1..N
  misplaced         (--plan) part K item j is the original invariant the plan maps there
  ref_mismatch      (--plan) its references equal the plan's rewrite (same part -> new
                    number, earlier part -> "<part-dir> invariant M")
  later_ref / unknown_ref / bad_ref
                    every "<part-dir> invariant N" citation names an earlier part, with N
                    in range
  prose_added       every sentence outside Behavior / Assumes / Must not regress occurs in
                    the original, except one-line "Covered by <part-dir>." pointers
  citation_extra    Assumes and Must not regress hold only "- <part-dir> invariant N" lines

Output: key=value lines on stdout, first line status=pass|fail|count|error. Exit 0 on
pass/count, 1 on fail, 2 on error.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specparts import (CITATION, LIST_MARKER, RefError, Spec, die, heading, load_json,  # noqa: E402
                       mask, norm, rewrite_refs)
from collections import Counter  # noqa: E402

POINTER = re.compile(r"^Covered by `?[\w.\-/]+`?\.$")
CITE_LINE = re.compile(r"^[-*+]\s+`?[\w.\-]+-\d{2}-[\w\-]+`?\s+invariant\s+\d+\s*$")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
NON_PROSE = {"assumes", "must not regress"}


def flat(lines):
    """Prose text with list markers stripped and whitespace collapsed."""
    return norm(" ".join(LIST_MARKER.sub("", l) for l in lines if not heading(l)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", required=True)
    ap.add_argument("--part", action="append", default=[])
    ap.add_argument("--plan")
    ap.add_argument("--expect-counts", default="")
    a = ap.parse_args()

    orig = Spec(a.original)
    if not orig.items:
        die(f"Behavior section in {a.original} has no numbered items",
            "check the spec has a numbered list under its Behavior heading")
    if not a.part:
        print("status=count")
        print(f"invariants={len(orig.items)}")
        return 0

    parts = []
    for p in a.part:
        path = os.path.join(p, "functional-spec.md") if os.path.isdir(p) else p
        parts.append((os.path.basename(os.path.dirname(os.path.abspath(path))), Spec(path)))
    index = {name: k for k, (name, _) in enumerate(parts, 1)}
    sizes = {name: len(s.items) for name, s in parts}
    dirs = {k: name for name, k in index.items()}
    problems = []

    plan = load_json(a.plan, "plan") if a.plan else None
    if plan and len(plan["parts"]) != len(parts):
        die(f"plan has {len(plan['parts'])} parts, {len(parts)} --part given",
            "pass every part directory, in chain order")
    expected = [int(x) for x in a.expect_counts.split(",")] if a.expect_counts else []
    if plan and not expected:
        expected = [len(p["invariants"]) for p in plan["parts"]]
    if expected and len(expected) != len(parts):
        die(f"--expect-counts has {len(expected)} values for {len(parts)} parts",
            "give one count per --part, in the same order")
    for (name, s), want in zip(parts, expected):
        if len(s.items) != want:
            problems.append(f"count part={name} found={len(s.items)} expected={want}")

    for name, s in parts:
        for pos, label in s.numbering_problems():
            problems.append(f"numbering part={name} position={pos} label={label}")

    pool = Counter(mask(it.text) for it in orig.items)
    seen = Counter()
    for name, s in parts:
        for n, it in enumerate(s.items, 1):
            key = mask(it.text)
            seen[key] += 1
            if seen[key] > pool[key]:
                problems.append(f'extra part={name} new={n} text="{it.text[:120]}"')
    for n, it in enumerate(orig.items, 1):
        key = mask(it.text)
        if seen[key] < pool[key]:
            problems.append(f'missing original={n} text="{it.text[:120]}"')
            seen[key] += 1

    if plan:
        loc = {old: (p["index"], new) for p in plan["parts"] for new, old in enumerate(p["invariants"], 1)}
        for (name, s), p in zip(parts, plan["parts"]):
            k = index[name]
            for new, (it, old) in enumerate(zip(s.items, p["invariants"]), 1):
                src = orig.items[old - 1]
                if mask(it.text) != mask(src.text):
                    problems.append(f"misplaced part={name} new={new} expected_original={old}")
                    continue
                try:
                    want = norm(rewrite_refs(src.raw(), loc, k, dirs))
                except RefError as err:
                    problems.append(f'{err.kind} part={name} new={new} token="{err.token}"')
                    continue
                if it.text != want:
                    problems.append(f'ref_mismatch part={name} new={new} expected="{want[:120]}"')

    for name, s in parts:
        text = "\n".join(s.lines)
        for m in CITATION.finditer(text):
            cited = m.group(1)
            nums = [int(x) for x in re.split(r"\s*(?:,|and|or|&)\s*", m.group(2))]
            if cited not in index:
                problems.append(f"unknown_ref part={name} cites={cited}")
            elif index[cited] >= index[name]:
                problems.append(f"later_ref part={name} cites={cited}")
            else:
                for num in nums:
                    if not 1 <= num <= sizes[cited]:
                        problems.append(f"bad_ref part={name} cites={cited} invariant={num} max={sizes[cited]}")

    source = flat(orig.lines)
    for name, s in parts:
        for title, _, body in s.sections:
            if body is s.behavior[2]:
                continue
            if title.lower() in NON_PROSE:
                for line in body:
                    if line.strip() and not CITE_LINE.match(line.strip()):
                        problems.append(f'citation_extra part={name} section="{title}" text="{line.strip()[:120]}"')
                continue
            for line in body:
                if not line.strip() or heading(line):
                    continue
                stripped = norm(LIST_MARKER.sub("", line))
                if POINTER.match(stripped):
                    continue
                for sentence in SENTENCE.split(stripped):
                    if sentence and sentence not in source:
                        problems.append(f'prose_added part={name} section="{title}" text="{sentence[:120]}"')

    print("status=fail" if problems else "status=pass")
    print(f"parts={len(parts)} invariants={len(orig.items)}")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
