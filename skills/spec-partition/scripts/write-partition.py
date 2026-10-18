#!/usr/bin/env python3
"""Write the part specs, initiative stubs and partition.md from an approved plan.

Usage:
  write-partition.py --original <functional-spec.md> --plan <plan.json> --prose <prose.json>
                     [--overwrite]

prose.json (written by the agent; the only judgment input), one entry per plan part in
chain order:
  {"parts": [{"slug": "core",
              "scope": "Paragraph copied from the original initiative.md.",
              "sections": {"Summary": "Sentences copied from the original.",
                           "Non-goals": "- Sync.\\nCovered by foo-02-export."}}]}
  Section names must be original non-Behavior section titles. Empty text omits a section.

Behavior items are copied from the original byte for byte and renumbered; every
"invariant N" token is rewritten (same part -> new number, earlier part ->
"<part-dir> invariant M"). Assumes comes from cross-part edges in the plan, Must not
regress from the plan's crosscutting list. Part dirs are siblings of the original
initiative: <name>-<NN>-<slug>. Everything is validated before the first write.

Output: key=value lines, first line status=written|exists|fail|error.
Exit 0 written, 1 fail (reference problems, nothing written), 2 error, 3 exists (rerun
with --overwrite after the user approves).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specparts import RefError, Spec, die, heading, is_weak, load_json, read, rewrite_refs  # noqa: E402

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED = {"assumes", "must not regress"}


def head(level, title):
    return f"**{title}**" if level == 0 else "#" * level + " " + title


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--prose", required=True)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()

    spec = Spec(a.original)
    plan = load_json(a.plan, "plan")
    prose = load_json(a.prose, "prose").get("parts", [])
    src_dir = os.path.dirname(os.path.abspath(a.original))
    name, base = os.path.basename(src_dir), os.path.dirname(src_dir)
    parts = plan["parts"]

    if plan["invariants"] != len(spec.items):
        die(f"plan has {plan['invariants']} invariants, original has {len(spec.items)}",
            "the original changed since planning; rerun plan-partition.py")
    if plan["decision"] != "split":
        die(f"plan decision is {plan['decision']} ({plan['reason']})", "only a split plan can be written")
    if len(prose) != len(parts):
        die(f"prose.json has {len(prose)} parts, plan has {len(parts)}",
            "add one prose entry per plan part, in chain order")
    slugs = [p.get("slug", "") for p in prose]
    if not all(SLUG.match(s) for s in slugs) or len(set(slugs)) != len(slugs):
        die(f"slugs {slugs} must be unique kebab-case", "fix the slug fields in prose.json")
    titles = {s[0].lower(): s for s in spec.sections if s is not spec.behavior}
    for p in prose:
        for t in p.get("sections", {}):
            if t.lower() not in titles or t.lower() in RESERVED:
                die(f"prose section '{t}' is not an original non-Behavior section",
                    f"use one of: {', '.join(s[0] for s in titles.values())}")

    dirs = {i: f"{name}-{i:02d}-{slug}" for i, slug in enumerate(slugs, 1)}
    loc = {old: (p["index"], new) for p in parts for new, old in enumerate(p["invariants"], 1)}
    cross = sorted(set(plan["crosscutting"]))

    files, problems = {}, []
    for p, pr in zip(parts, prose):
        k, lvl = p["index"], spec.level
        assumes = sorted({loc[e["to"]] for e in plan["edges"]
                          if e["directed"] and loc[e["from"]][0] == k and loc[e["to"]][0] < k})
        regress = sorted({loc[c] for c in cross if loc[c][0] < k})
        out = []
        if spec.title:
            out += [f"# {spec.title} (part {k:02d}: {pr['slug']})", ""]
        for title, line, _ in spec.sections:
            if spec.behavior and line == spec.behavior[1]:
                if assumes:
                    out += [head(lvl, "Assumes"), ""] + [f"- {dirs[q]} invariant {n}" for q, n in assumes] + [""]
                out += [line, ""]
                sub = None
                for new, old in enumerate(p["invariants"], 1):
                    item = spec.items[old - 1]
                    if item.sub and item.sub != sub:
                        out += ([""] if out[-1] else []) + [item.sub, ""]
                    sub = item.sub
                    try:
                        out.append(f"{new}. " + rewrite_refs(item.raw(), loc, k, dirs))
                    except RefError as err:
                        problems.append(f'{err.kind} part={dirs[k]} original={old} token="{err.token}"')
                out.append("")
                if regress:
                    out += [head(lvl, "Must not regress"), ""] + [f"- {dirs[q]} invariant {n}" for q, n in regress] + [""]
                continue
            text = next((v for t, v in pr.get("sections", {}).items() if t.lower() == title.lower()), "")
            if text.strip():
                out += [line, "", text.strip(), ""]
        files[os.path.join(base, dirs[k], "functional-spec.md")] = "\n".join(out).rstrip() + "\n"

        init = os.path.join(src_dir, "initiative.md")
        link = "initiative.md" if os.path.exists(init) else "functional-spec.md"
        ititle = name
        if os.path.exists(init):
            ititle = next((h[1] for h in map(heading, read(init).splitlines()) if h and h[0] == 1), name)
        files[os.path.join(base, dirs[k], "initiative.md")] = (
            f"# {ititle} (part {k:02d}: {pr['slug']})\n\n{pr.get('scope', '').strip()}\n\n"
            f"Part of [{name}](../{name}/{link}).\n")

    if problems:
        print("status=fail")
        for pr in problems:
            print(pr)
        print("hint=rewrite the reference in the original with /spec-functional, or adjust the plan "
              "(--join/--move) so the cited invariants share a part or sit in earlier parts")
        return 1

    lines = [f"# Partition of {name}", "", "## Parts (implementation order)", ""]
    for p in parts:
        k = p["index"]
        assumes = ", ".join(f"`{dirs[q]}`" for q in p["assumes"]) or "none"
        flags = f"; flags: {', '.join(p['flags'])}" if p["flags"] else ""
        lines.append(f"{k}. `{dirs[k]}`: {len(p['invariants'])} invariants; assumes: {assumes}{flags}")
    lines += ["", "## Invariant mapping", "", "| old | part-dir | new |", "|---|---|---|"]
    for old in sorted(loc):
        q, n = loc[old]
        lines.append(f"| {old} | {dirs[q]} | {n} |")
    for title, keep in (("Cross-part edges", False), ("Kept apart despite link", True)):
        rows = [e for e in plan["edges"] if loc[e["from"]][0] != loc[e["to"]][0] and is_weak(e) == keep]
        lines += ["", f"## {title}", ""]
        if rows:
            lines += ["| from | to | parts | rules | evidence |", "|---|---|---|---|---|"]
            lines += [f"| {e['from']} | {e['to']} | {loc[e['from']][0]} → {loc[e['to']][0]} | "
                      f"{', '.join(e['rules'])} | {e['evidence']} |" for e in rows]
        else:
            lines.append("None.")
    lines += ["", "## Implementation order", ""]
    lines += [f"{p['index']}. /spec-technical {dirs[p['index']]}" for p in parts]
    files[os.path.join(src_dir, "partition.md")] = "\n".join(lines) + "\n"

    targets = [os.path.join(base, d) for d in dirs.values()]
    existing = [d for d in targets if os.path.isdir(d) and os.listdir(d)]
    if os.path.exists(os.path.join(src_dir, "partition.md")):
        existing.append(os.path.join(src_dir, "partition.md"))
    if existing and not a.overwrite:
        print("status=exists")
        for e in existing:
            print(f"path={e}")
        print("hint=ask the user to approve overwriting, then rerun with --overwrite")
        return 3

    written = []
    for path, content in files.items():
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
        except OSError as e:
            print("status=error")
            print(f"message=cannot write {path}: {e.strerror}")
            for w in written:
                print(f"written={w}")
            print("hint=fix the cause and rerun with --overwrite; output is regenerated from the plan")
            return 2
        written.append(path)
    print("status=written")
    for k in sorted(dirs):
        print(f"part={k} dir={os.path.join(base, dirs[k])}")
    print(f"partition={os.path.join(src_dir, 'partition.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
