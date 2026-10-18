#!/usr/bin/env python3
"""Compute a spec-partition plan from an invariant dependency graph.

Usage:
  plan-partition.py --original <functional-spec.md> --graph <graph.json> --out <plan.json>
                    [--join A:B ...] [--move A:B ...]

graph.json (written by the agent; the only judgment input):
  {"edges": [{"from": 12, "to": 3, "rules": ["code"], "evidence": "E_EMPTY",
              "directed": true, "codes": 1}],
   "crosscutting": [5]}
  from = dependent, to = prerequisite (old numbers). directed defaults to true.
  rules: ref, code, order, state, output, fixture. codes = number of shared error codes
  (default 1). Explicit "invariant N" citations in the original are added as ref edges
  automatically.

Algorithm: undirected strong edges (anything but fixture-only or a single shared code)
join invariants into components; directed edges (B needs A) never join, they only order,
so they may cross parts as long as they point backward. --join A:B puts A and B in one
part; --move A:B puts A alone into B's part. Components that depend on each other in a
cycle are merged into cores; when a merge exceeds 30, single (then paired) moves that
avoid it are listed as candidates. Parts under 8 merge into the neighbor they share most
edges with, unless that creates a cycle or they have no edges (flagged). Parts are ordered
prerequisites first; ties: fewer prerequisite parts, then lowest original invariant, then
smaller.

Decision: fewer than 16 invariants -> no-split (too_few); one part -> no-split
(single_part); 40 or fewer invariants -> split only if two or more cores have 8+
invariants each (else no_clean_cut); above 40 -> split.

Output: key=value lines on stdout (status=ok|error first) and the plan JSON at --out.
Exit 0 on ok, 2 on error.
"""
import argparse
import json
import os
import sys
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specparts import REF, Spec, die, is_weak, load_json, ref_numbers  # noqa: E402

RULES = {"ref", "code", "order", "state", "output", "fixture"}
MIN, MAX = 8, 30


def pairs(values, flag):
    out = []
    for v in values:
        try:
            a, b = (int(x) for x in v.split(":"))
        except ValueError:
            die(f"{flag} {v} is not A:B", f"use old invariant numbers, e.g. {flag} 12:3")
        out.append((a, b))
    return out


def load_edges(spec, graph):
    n = len(spec.items)
    edges = []
    for i, e in enumerate(graph.get("edges", []), 1):
        bad = None
        if not all(isinstance(e.get(k), int) and 1 <= e[k] <= n for k in ("from", "to")):
            bad = f"from/to must be invariant numbers 1..{n}"
        elif e["from"] == e["to"]:
            bad = "from and to are the same invariant"
        elif not e.get("rules") or not set(e["rules"]) <= RULES:
            bad = f"rules must be a non-empty subset of {sorted(RULES)}"
        elif not str(e.get("evidence", "")).strip():
            bad = "evidence is empty; name the shared term, code or state"
        if bad:
            die(f"graph edge {i} invalid: {bad}", "fix the edge in graph.json and rerun")
        edges.append({"from": e["from"], "to": e["to"], "rules": sorted(set(e["rules"])),
                      "evidence": e["evidence"], "directed": e.get("directed", True),
                      "codes": e.get("codes", 1)})
    index = {(e["from"], e["to"]): e for e in edges}
    for pos, item in enumerate(spec.items, 1):
        for m in REF.finditer(item.text):
            for o in ref_numbers(m.group(3)):
                if not 1 <= o <= n:
                    die(f"original invariant {pos} cites invariant {o}, which does not exist",
                        "fix the reference in the original functional-spec.md with /spec-functional")
                if o == pos:
                    continue
                e = index.get((pos, o))
                if e:
                    e["rules"] = sorted(set(e["rules"]) | {"ref"})
                    e["directed"] = True
                else:
                    e = {"from": pos, "to": o, "rules": ["ref"], "directed": True, "codes": 1,
                         "evidence": f"invariant {pos} cites invariant {o}"}
                    edges.append(e)
                    index[(pos, o)] = e
    return edges


def components(n, edges, joins, moves):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    moved = {a for a, _ in moves}
    for e in edges:
        if not is_weak(e) and not e["directed"] and e["from"] not in moved and e["to"] not in moved:
            union(e["from"], e["to"])
    for a, b in joins:
        union(a, b)
    for a, b in moves:
        parent[a] = find(b)
    groups = {}
    for i in range(1, n + 1):
        groups.setdefault(find(i), set()).add(i)
    return list(groups.values())


def owner(parts):
    return {i: k for k, p in enumerate(parts) for i in p}


def deps(parts, edges):
    """Directed part graph: dependent part -> set of prerequisite parts."""
    own = owner(parts)
    out = {k: set() for k in range(len(parts))}
    for e in edges:
        a, b = own[e["from"]], own[e["to"]]
        if e["directed"] and a != b:
            out[a].add(b)
    return out


def sccs(graph):
    index, low, stack, on, out, counter = {}, {}, [], set(), [], [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph[v]:
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = set()
            while True:
                w = stack.pop()
                on.discard(w)
                comp.add(w)
                if w == v:
                    break
            out.append(comp)

    for v in graph:
        if v not in index:
            visit(v)
    return out


def merge_cycles(parts, edges):
    merges, result = [], []
    for scc in sccs(deps(parts, edges)):
        merged = set().union(*(parts[k] for k in scc))
        if len(scc) > 1:
            merges.append({"invariants": sorted(merged), "size": len(merged),
                           "from_parts": [sorted(parts[k]) for k in scc]})
        result.append(merged)
    return result, merges


def acyclic(parts, edges):
    return all(len(s) == 1 for s in sccs(deps(parts, edges)))


def edge_count(parts, edges, a, b):
    own = owner(parts)
    return sum(1 for e in edges if {own[e["from"]], own[e["to"]]} == {a, b})


def merge_small(parts, edges):
    flags = {}
    while True:
        small = [k for k, p in enumerate(parts) if len(p) < MIN and frozenset(p) not in flags]
        if not small:
            return parts, flags
        k = min(small, key=lambda k: (len(parts[k]), min(parts[k])))
        neighbors = [j for j in range(len(parts)) if j != k and edge_count(parts, edges, k, j)]
        neighbors.sort(key=lambda j: (-edge_count(parts, edges, k, j), len(parts[j]), min(parts[j])))
        for j in neighbors:
            trial = [p for i, p in enumerate(parts) if i not in (k, j)] + [parts[k] | parts[j]]
            if acyclic(trial, edges):
                parts = trial
                break
        else:
            flags[frozenset(parts[k])] = "small_unmerged" if neighbors else "independent"


def build(n, edges, joins, moves):
    """Parts after small-part merging, cycle merges, flags, and the cohesive cores
    (components after cycle merging, before small parts are folded in)."""
    cores, merges = merge_cycles(components(n, edges, joins, moves), edges)
    parts, flags = merge_small(cores, edges)
    return parts, merges, flags, cores


def oversized_merge(merges):
    return any(m["size"] > MAX for m in merges)


def candidates(n, edges, joins, moves, merges):
    found = []
    for m in (m for m in merges if m["size"] > MAX):
        options = []
        for group in m["from_parts"]:
            for v in group:
                for target in m["from_parts"]:
                    if target is not group:
                        options.append((v, min(target)))
        for (v, t) in options:
            _, trial, _, _ = build(n, edges, joins, moves + [(v, t)])
            if not oversized_merge(trial):
                found.append([f"{v}:{t}"])
        if not found:
            for (a, b) in combinations(options, 2):
                if a[0] == b[0]:
                    continue
                _, trial, _, _ = build(n, edges, joins, moves + [a, b])
                if not oversized_merge(trial):
                    found.append([f"{a[0]}:{a[1]}", f"{b[0]}:{b[1]}"])
                    if len(found) >= 5:
                        break
    return found[:5]


def order(parts, edges):
    graph = deps(parts, edges)
    placed, seq = set(), []
    while len(seq) < len(parts):
        ready = [k for k in range(len(parts)) if k not in placed and graph[k] <= placed]
        k = min(ready, key=lambda k: (len(graph[k]), min(parts[k]), len(parts[k])))
        placed.add(k)
        seq.append(k)
    return seq, graph


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--original", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--join", action="append", default=[])
    ap.add_argument("--move", action="append", default=[])
    a = ap.parse_args()

    spec = Spec(a.original)
    n = len(spec.items)
    if not n:
        die(f"Behavior section in {a.original} has no numbered items", "check the spec has a numbered Behavior list")
    if spec.numbering_problems():
        pos, label = spec.numbering_problems()[0]
        die(f"Behavior item at position {pos} is labeled {label}",
            "number the original Behavior list 1..N continuously with /spec-functional, then rerun")
    graph = load_json(a.graph, "graph")
    edges = load_edges(spec, graph)
    joins, moves = pairs(a.join, "--join"), pairs(a.move, "--move")
    for x, y in joins + moves:
        if not (1 <= x <= n and 1 <= y <= n) or x == y:
            die(f"--join/--move {x}:{y} is out of range", f"use two different old numbers in 1..{n}")
    moved = {x for x, _ in moves}
    if any(x in moved or y in moved for x, y in joins) or any(y in moved for _, y in moves):
        die("a moved invariant also appears in a --join or as a --move target",
            "move each invariant once, and name an unmoved invariant as the target")
    crosscutting = graph.get("crosscutting", [])
    if not all(isinstance(c, int) and 1 <= c <= n for c in crosscutting):
        die(f"crosscutting must list invariant numbers 1..{n}", "fix crosscutting in graph.json")

    parts, merges, flags, cores = build(n, edges, joins, moves)
    seq, graph_k = order(parts, edges)
    pos = {k: i + 1 for i, k in enumerate(seq)}
    ordered = [parts[k] for k in seq]
    own = {i: pos[k] for k, p in enumerate(parts) for i in p}

    if n < 2 * MIN:
        decision, reason = "no-split", "too_few"
    elif len(parts) < 2:
        decision, reason = "no-split", "single_part"
    elif n <= 40 and sum(1 for c in cores if len(c) >= MIN) < 2:
        decision, reason = "no-split", "no_clean_cut"
    else:
        decision, reason = "split", ""

    plan_parts = []
    for i, k in enumerate(seq, 1):
        f = [flags[frozenset(parts[k])]] if frozenset(parts[k]) in flags else []
        if len(parts[k]) > MAX:
            f.append("oversized")
        plan_parts.append({"index": i, "invariants": sorted(parts[k]),
                           "assumes": sorted(pos[j] for j in graph_k[k]), "flags": f})
    for e in edges:
        e["parts"] = [own[e["from"]], own[e["to"]]]
    cands = candidates(n, edges, joins, moves, merges) if oversized_merge(merges) else []
    plan = {"original": os.path.abspath(a.original), "invariants": n, "decision": decision,
            "reason": reason, "parts": plan_parts, "edges": edges,
            "crosscutting": sorted(set(crosscutting)), "cycle_merges": merges,
            "cycle_break_candidates": cands, "joins": a.join, "moves": a.move}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2)
    except OSError as e:
        die(f"cannot write {a.out}: {e.strerror}", "choose a writable --out path")

    print("status=ok")
    print(f"decision={decision}" + (f" reason={reason}" if reason else "") + f" invariants={n} parts={len(ordered)}")
    for p in plan_parts:
        print(f"part={p['index']} size={len(p['invariants'])} assumes={','.join(map(str, p['assumes']))} "
              f"flags={','.join(p['flags'])} invariants={','.join(map(str, p['invariants']))}")
    for e in edges:
        if e["parts"][0] != e["parts"][1]:
            kind = "weak_kept_apart" if is_weak(e) else "cross_edge"
            print(f'{kind} from={e["from"]} to={e["to"]} parts={e["parts"][0]}->{e["parts"][1]} '
                  f'rules={",".join(e["rules"])} directed={str(e["directed"]).lower()} '
                  f'evidence="{e["evidence"]}"')
    for m in merges:
        print(f"cycle_merge size={m['size']} invariants={','.join(map(str, m['invariants']))}")
    for c in cands:
        print("cycle_break_candidate " + " ".join(f"--move {x}" for x in c))
    print(f"plan={os.path.abspath(a.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
