#!/usr/bin/env python3
"""Parse auto-verify reports.

Usage: auto.py parse --kind static|dynamic --report PATH

Output (key=value):
  static:  status=ok total=<n> covered=<1,3> uncovered=<2>
  dynamic: status=ok total=<n> passed=<1> failed=<2> skipped=<3,4>
           skip_reasons=<3:reason;4:reason>
  Lists hold invariant numbers. Fails closed: an empty report or an unrecognized
  verdict is an error, never a guess.

Usage: auto.py decide --round N --acted N --open <1,2> [--prev-open <1,2>]

Output (key=value, one per line; checks run in this order):
  decide:  status=stop reason=clean   (nothing open and no actions taken)
           status=stop reason=no-progress   (nothing acted and no --prev-open given, or the open set equals --prev-open)
           status=stop reason=bound   (round reached the maximum with invariants still open)
           status=continue

Usage: auto.py summary --log PATH

Output (key=value):
  summary: status=ok tests_added=<n> corrections=<n> skipped=<n>
           skipped_by_reason=<reason>:<count>;...   (counted in the latest run block; reasons in order of first appearance)
           regression=true|false   (true if any entry line in the latest run block ends with ` [regression]`)
           dynamic=performed|skipped   (skipped if the latest run block has a `- [rN] note: dynamic skipped: <reason>` line)
           dynamic_reason=<reason>   (empty when dynamic=performed)
           needs_review=true|false   (true if any `- [rN] note: ...` line in the latest run block contains `auto-generated`)
  Dies when the log has no run block.

Usage: auto.py next --log PATH
       auto.py advance --log PATH --result JSON

  The state machine (machine.py) that drives an auto run. `next` prints state=, round=, action=,
  result_schema= and state-specific fields; at SUMMARY it also prints the summary counts.
  `advance` validates the result for the current state, appends the event, entries and notes
  to the log, and prints the new state=/round=. An invalid result is status=error and writes nothing.

Errors: status=error/message=/hint= on stdout, exit 2.
"""
import argparse
import json
import os
import re

import machine as M
import speclog as S


class ReportError(ValueError):
    def __init__(self, message, hint):
        super().__init__(message)
        self.hint = hint


def scan_invariants(text, label):
    """Yield (invariant number, value) for each `<label>:` line in an invariant block."""
    current = None
    for line in text.splitlines():
        m = re.match(r"Invariant (\d+) —", line)
        if m:
            current = int(m.group(1))
        elif current is not None and line.strip().startswith(label + ":"):
            yield current, line.strip()[len(label) + 1:].strip()
            current = None


def parse_static(text):
    covered, uncovered = [], []
    for n, value in scan_invariants(text, "Static"):
        if value.startswith("covered"):
            covered.append(n)
        elif value.startswith("no coverage found"):
            uncovered.append(n)
        else:
            raise ReportError(f"invariant {n} has unrecognized static verdict '{value}'",
                              "the report format may have drifted; re-run /spec-verify-static or check auto.py's parser")
    return covered, uncovered


def parse_dynamic(text):
    passed, failed, skipped, reasons = [], [], [], []
    for n, value in scan_invariants(text, "Dynamic"):
        if value.startswith("pass"):
            passed.append(n)
        elif value.startswith("fail"):
            failed.append(n)
        elif value.startswith("skip —") and value.split("—", 1)[1].strip():
            skipped.append(n)
            reasons.append(f"{n}:{value.split('—', 1)[1].strip()}")
        else:
            raise ReportError(f"invariant {n} has unrecognized dynamic verdict '{value}'",
                              "the report format may have drifted; re-run /spec-verify-dynamic or check auto.py's parser")
    return passed, failed, skipped, reasons


def csv(numbers):
    return ",".join(map(str, numbers))


def load_report(kind, path):
    """Parsed report as a dict of lists; raises ReportError."""
    text = S.read(path)
    if not re.search(r"^Invariant \d+ —", text, re.M):
        raise ReportError(f"{path} has no invariants",
                          f"the report may be empty or its format drifted; re-run /spec-verify-{kind}")
    if kind == "dynamic":
        passed, failed, skipped, reasons = parse_dynamic(text)
        return dict(passed=passed, failed=failed,
                    skipped=[[n, r.split(":", 1)[1]] for n, r in zip(skipped, reasons)],
                    reasons=reasons)
    covered, uncovered = parse_static(text)
    return dict(covered=covered, uncovered=uncovered)


def cmd_parse(a):
    try:
        r = load_report(a.kind, a.report)
    except ReportError as e:
        S.die(str(e), e.hint)
    if a.kind == "dynamic":
        S.out(total=len(r["passed"]) + len(r["failed"]) + len(r["skipped"]),
              passed=csv(r["passed"]), failed=csv(r["failed"]), skipped=csv([n for n, _ in r["skipped"]]),
              skip_reasons=";".join(r["reasons"]))
        return
    S.out(total=len(r["covered"]) + len(r["uncovered"]),
          covered=csv(r["covered"]), uncovered=csv(r["uncovered"]))


def stop(reason):
    print("status=stop")
    print(f"reason={reason}")


def number_set(text):
    return {int(n) for n in text.split(",") if n.strip()}


def cmd_decide(a):
    reason = M.decide(a.round, a.acted, number_set(a.open),
                      None if a.prev_open is None else number_set(a.prev_open))
    if reason:
        return stop(reason)
    print("status=continue")


def distinct_actions(lines, action):
    """One fix applied to several findings is one action: count by [fix: id], else by identical reason and files."""
    keys = set()
    for line in lines:
        if f"[action: {action}]" in line:
            m = re.search(r"\[fix: ([^\]]+)\]", line)
            keys.add(m.group(1) if m else line.split(" — ", 1)[-1])
    return len(keys)


def summarize(text):
    lines = S.latest_run(text).splitlines()
    reasons = {}
    for line in lines:
        m = re.search(r" — skipped: (.*?)(?: \[|$)", line)
        if m:
            reasons[m.group(1)] = reasons.get(m.group(1), 0) + 1
    dynamic_reason = None
    for line in lines:
        m = re.match(r"- \[r\d+\] note: dynamic skipped: (.*)$", line)
        if m:
            dynamic_reason = m.group(1).strip()
    dynamic = "performed" if dynamic_reason is None else "skipped"
    failure = next((line for line in lines if "note: delegated-step failure" in line), None)
    if dynamic_reason is None and failure and not any("/dynamic]" in line for line in lines):
        dynamic, dynamic_reason = "not-run", failure.split("note: ", 1)[1].strip()
    return dict(tests_added=distinct_actions(lines, "test"),
                corrections=distinct_actions(lines, "correction"),
                skipped=sum(reasons.values()),
                skipped_by_reason=";".join(f"{r}:{c}" for r, c in reasons.items()),
                regression=str(any(line.endswith(" [regression]") for line in lines)).lower(),
                dynamic=dynamic,
                dynamic_reason=dynamic_reason or "",
                needs_review=str(any(re.match(r"- \[r\d+\] note: recipe \S+ auto-generated", line)
                                     for line in lines)).lower())


def cmd_summary(a):
    text = S.read(a.log)
    if "### Run" not in text:
        S.die(f"{a.log} has no auto-verification run", "run 'auto-start' first")
    S.out(**summarize(text))


def run_block(path):
    text = S.read(path)
    if "### Run" not in text:
        S.die(f"{path} has no auto-verification run", "run 'auto-start' first")
    return text, S.latest_run(text)


def spec_texts(log_path):
    spec = os.path.join(os.path.dirname(os.path.abspath(log_path)), "functional-spec.md")
    return M.invariant_texts(S.read(spec))


def cmd_next(a):
    text, block = run_block(a.log)
    ctx = M.replay(block)
    texts = spec_texts(a.log) if ctx["state"] in ("ACT_TEST", "CORRECT") else {}
    pairs = M.describe(ctx, texts)
    if ctx["state"] == "SUMMARY":
        pairs += list(summarize(text).items())
    S.out(**dict(pairs))


def entry_line(ctx, texts, fx):
    if fx["inv"] not in texts:
        S.die(f"invariant {fx['inv']} is not a numbered Behavior item in functional-spec.md",
              "the result named an invariant that does not exist")
    return S.format_entry(ctx["r"], fx["stage"], fx["inv"], texts[fx["inv"]], fx["decision"], fx["reason"],
                          files=fx["files"], action=fx["action"], regression=fx["regression"],
                          fix_id=fx["fix_id"])


def cmd_advance(a):
    text, block = run_block(a.log)
    ctx = M.replay(block)
    try:
        payload = M.normalize(ctx, json.loads(a.result), load_report)
    except (ValueError, json.JSONDecodeError) as e:
        S.die(f"invalid result for state {ctx['state']}: {e}", f"expected {M.SCHEMAS[ctx['state']]}")
    new_ctx, effects = M.step(ctx, payload)
    texts = spec_texts(a.log) if any(fx["kind"] == "entry" for fx in effects) else {}
    lines = [M.event_line(ctx, payload)]
    seen = block
    for fx in effects:
        if fx["kind"] == "note":
            lines.append(f"- [r{ctx['r']}] note: {fx['text']}")
            continue
        if S.has_entry(seen, ctx["r"], fx["stage"], fx["inv"]):
            continue
        line = entry_line(ctx, texts, fx)
        seen += "\n" + line
        lines.append(line)
    S.write(a.log, text.rstrip("\n") + "\n" + "\n".join(lines) + "\n")
    S.out(state=new_ctx["state"], round=new_ctx["r"])




def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pp = sub.add_parser("parse")
    pp.add_argument("--kind", required=True, choices=["static", "dynamic"])
    pp.add_argument("--report", required=True)
    pp.set_defaults(fn=cmd_parse)
    pd = sub.add_parser("decide")
    pd.add_argument("--round", type=int, required=True)
    pd.add_argument("--acted", type=int, required=True)
    pd.add_argument("--open", required=True)
    pd.add_argument("--prev-open", default=None)
    pd.set_defaults(fn=cmd_decide)
    ps = sub.add_parser("summary")
    ps.add_argument("--log", required=True)
    ps.set_defaults(fn=cmd_summary)
    pn = sub.add_parser("next")
    pn.add_argument("--log", required=True)
    pn.set_defaults(fn=cmd_next)
    pv = sub.add_parser("advance")
    pv.add_argument("--log", required=True)
    pv.add_argument("--result", required=True)
    pv.set_defaults(fn=cmd_advance)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
