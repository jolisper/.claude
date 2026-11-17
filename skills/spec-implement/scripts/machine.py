"""Auto-verify state machine.

Not a CLI: imported by auto.py (`next`, `advance`). The run's state is rebuilt by replaying
the `- [rN] event: <STATE> <json>` lines of the latest run block through `step`, so the
logbook is the only memory and a resumed run sees the same state (38).

`step` is pure: (ctx, normalized payload) -> (ctx, effects). Effects are log entries and
notes that `advance` appends together with the event. States that need no judgment (the
per-round decision) are entered and left inside one `step`, so the orchestrator only ever
sees a state that needs its action.
"""
import copy
import json
import re

import speclog as S

EVENT = re.compile(r"^- \[r\d+\] event: (\w+) (.*)$")
DEP_CLASSES = {"local", "development", "production", "unknown"}
TRIAGE_CLASSES = {"defect", "flaky", "environment", "spec-mismatch"}
SPEC_FILES = ("functional-spec.md", "technical-spec.md")
TERMINAL = {"SUMMARY", "DONE"}

SCHEMAS = {
    "INIT": '{"baseline": "green|red|broken"}',
    "STATIC_RUN": '{"report": "<path to verify-static-report.md>"}',
    "STATIC_CLASSIFY": '{"testable": [2], "deferred": [{"inv": 3, "why": "<why not statically testable>"}]}',
    "ACT_TEST": '{"inv": 2, "outcome": "already-green|green", "files": ["<test file>"], "fix_id": "<id>", "regression": false}',
    "DYN_PREFLIGHT": '{"recipe": "<name>|null", "how": "existing|chosen", "why": "<optional>"}',
    "RECIPE_GEN": '{"recipe": "<name>", "route": "a|b"} or {"failed": "<why>"}',
    "DEP_GATE": '{"deps": [{"name": "db", "class": "local|development|production|unknown"}], "started": true}',
    "DYN_RUN": '{"report": "<path to verify-dynamic-report.md>"}',
    "TRIAGE": '{"findings": [{"inv": 2, "class": "defect|flaky|environment|spec-mismatch", "evidence": "<text>", "files": ["<defects only>"]}]}',
    "CORRECT": '{"inv": 2, "files": ["<changed file>"], "fix_id": "<id>", "route": "tdd|fallback", "regression": false}',
    "SUMMARY": "{}",
    "DONE": "(none)",
}

ACTIONS = {
    "INIT": "Run every layer's runner (baseline). Report green, red, or broken.",
    "STATIC_RUN": "Launch the 'Static verify' agent template, then advance with the report path.",
    "STATIC_CLASSIFY": "Classify each uncovered invariant as statically testable or not; together they must be exactly the uncovered set.",
    "ACT_TEST": "Run the coverage-gap cycle for the invariant below (tdd-red, then green/refactor only if genuinely red), then the regression check.",
    "DYN_PREFLIGHT": "Glob .claude/skills/run-*/SKILL.md. One recipe: report it. Several: choose by the spec-verify-dynamic comparison and say why. None: recipe=null.",
    "RECIPE_GEN": "Launch the 'Recipe generation' agent template once. Report the recipe and route, or why it failed.",
    "DEP_GATE": "Launch the 'Dynamic verify' agent template up to the dependency map and report every dependency with its class. started=false if the app did not start.",
    "DYN_RUN": "Let the dynamic-verify agent finish, then advance with the report path.",
    "TRIAGE": "Triage each failed invariant into exactly one class. Defects need the files the finding implicates.",
    "CORRECT": "Run the correction cycle for the invariant below, scoped to the listed files, then the regression check.",
    "SUMMARY": "Print the counts, the open list and the stop reason below, point at logbook.md, then advance with {}.",
    "DONE": "Nothing left to do.",
}


def new_ctx():
    return dict(state="INIT", r=1, closing=False, acted=0, queue=[], files={}, uncovered=[], testable=[],
                deferred=[], tested=[], passed=[], failed=[], corrected=[], prev_open=None, recipe=None,
                gen_tried=False, dyn_skipped=False, stop=None, error=None, open=[],
                ever_passed=[], ever_corrected=[], verified=[], dyn_skips=[])


def decide(round, acted, open_, prev_open):
    """None to continue, else the stop reason. Checks run in this order."""
    if not open_ and acted == 0:
        return "clean"
    if acted == 0 and (prev_open is None or set(open_) == set(prev_open)):
        return "no-progress"
    if round >= S.MAX_ROUNDS:
        return "bound"
    return None


def replay(block):
    ctx = new_ctx()
    for line in block.splitlines():
        m = EVENT.match(line)
        if m:
            ctx, _ = step(ctx, json.loads(m.group(2)))
    return ctx


def entry(stage, inv, decision, reason, action=None, files=None, fix_id=None, regression=False):
    return dict(kind="entry", stage=stage, inv=inv, decision=decision, reason=reason, action=action,
                files=files, fix_id=fix_id, regression=regression)


def note(text):
    return dict(kind="note", text=text)


def fail(c, fx, message):
    c.update(state="SUMMARY", stop="failure", error=message)
    fx.append(note(f"delegated-step failure: {message}"))


def skip_dynamic(c, fx, reason):
    c["dyn_skipped"] = True
    fx.append(note(f"dynamic skipped: {reason}"))
    decide_round(c, fx)


def enter_preflight(c, fx):
    if c["recipe"]:
        c["state"] = "DEP_GATE"
    elif c["gen_tried"]:
        skip_dynamic(c, fx, "no recipe")
    else:
        c["state"] = "DYN_PREFLIGHT"


def decide_round(c, fx):
    open_ = sorted((set(c["testable"]) - set(c["tested"]))
                   | (set(c["deferred"]) - set(c["passed"]) - set(c["ever_passed"]))
                   | (set(c["failed"]) - set(c["corrected"])))
    reason = decide(c["r"], c["acted"], open_, c["prev_open"])
    c["open"] = open_
    if reason is None:
        c.update(r=c["r"] + 1, prev_open=open_, acted=0, queue=[], files={}, uncovered=[], testable=[],
                 deferred=[], tested=[], passed=[], failed=[], corrected=[], dyn_skipped=False,
                 state="STATIC_RUN")
    elif reason == "bound" and c["acted"] > 0:
        c.update(closing=True, state="STATIC_RUN")
    else:
        c.update(state="SUMMARY", stop=reason)


def verify_corrections(c, fx, p):
    """Track dynamic results across rounds and close the loop on earlier corrections."""
    for n in c["ever_corrected"]:
        if n in p["passed"] and n not in c["verified"]:
            c["verified"].append(n)
            fx.append(entry("dynamic", n, "verified", "re-verified after correction: pass"))
    c["ever_passed"] = sorted((set(c["ever_passed"]) - set(p["failed"])) | set(p["passed"]))
    c["dyn_skips"] = sorted(set(c["dyn_skips"]) | {n for n, *_ in p["skipped"]})


def closing_next(c):
    if c["dyn_skipped"] or not c["recipe"]:
        c.update(state="SUMMARY", stop="bound")
    else:
        c["state"] = "DEP_GATE"


def step(ctx, p):
    c = copy.deepcopy(ctx)
    fx = []
    s = c["state"]
    if "error" in p:
        fail(c, fx, p["error"])
        return c, fx
    if s == "INIT":
        if p["baseline"] == "green":
            c["state"] = "STATIC_RUN"
        else:
            fail(c, fx, f"baseline {p['baseline']}")
    elif s == "STATIC_RUN":
        c["uncovered"] = p["uncovered"]
        if c["closing"]:
            c["open"] = list(p["uncovered"])
            fx += [entry("static", n, "skipped", "closing verify: not acted on") for n in p["uncovered"]]
            closing_next(c)
        elif p["uncovered"]:
            c["state"] = "STATIC_CLASSIFY"
        else:
            enter_preflight(c, fx)
    elif s == "STATIC_CLASSIFY":
        c["testable"] = list(p["testable"])
        c["deferred"] = [d["inv"] for d in p["deferred"]]
        c["queue"] = list(p["testable"])
        for d in p["deferred"]:
            if d["inv"] not in c["ever_passed"]:
                fx.append(entry("static", d["inv"], "skipped", "deferred to dynamic"))
                fx.append(note(f"defer detail inv {d['inv']}: {d['why']}"))
        if c["queue"]:
            c["state"] = "ACT_TEST"
        else:
            enter_preflight(c, fx)
    elif s == "ACT_TEST":
        c["queue"].pop(0)
        c["tested"].append(p["inv"])
        c["acted"] += 1
        fx.append(entry("static", p["inv"], "acted", f"coverage-gap test ({p['outcome']})", "test",
                        p["files"], p["fix_id"], p["regression"]))
        if p["regression"]:
            c.update(state="SUMMARY", stop="regression")
            fx.append(note(f"regression after the test for inv {p['inv']}"))
        elif not c["queue"]:
            enter_preflight(c, fx)
    elif s == "DYN_PREFLIGHT":
        if p["recipe"]:
            c.update(recipe=p["recipe"], state="DEP_GATE")
            if p["how"] == "chosen":
                fx.append(note(f"recipe {p['recipe']} chosen: {p.get('why', 'best match')}"))
        else:
            c["state"] = "RECIPE_GEN"
    elif s == "RECIPE_GEN":
        c["gen_tried"] = True
        if "failed" in p:
            skip_dynamic(c, fx, f"no recipe could be generated: {p['failed']}")
        else:
            c.update(recipe=p["recipe"], state="DEP_GATE")
            fx.append(note(f"recipe {p['recipe']} auto-generated, needs review (route: {p['route']})"))
    elif s == "DEP_GATE":
        blocked = [d["name"] for d in p["deps"] if d["class"] in ("production", "unknown")]
        if blocked:
            c.update(state="SUMMARY", stop="safety")
            fx.append(note(f"safety stop: blocked on {', '.join(blocked)}"))
        elif not p["started"]:
            if c["closing"]:
                c.update(state="SUMMARY", stop="bound")
                fx.append(note("dynamic skipped: app did not start"))
            else:
                skip_dynamic(c, fx, "app did not start")
        else:
            c["state"] = "DYN_RUN"
    elif s == "DYN_RUN":
        c.update(passed=p["passed"], failed=p["failed"])
        verify_corrections(c, fx, p)
        if c["closing"]:
            c["open"] = sorted(set(c["open"]) | set(p["failed"]))
            fx += [entry("dynamic", n, "skipped", "closing verify: not acted on") for n in p["failed"]]
            c.update(state="SUMMARY", stop="bound")
        else:
            for n, reason, detail in p["skipped"]:
                fx.append(entry("dynamic", n, "skipped", reason))
                if detail:
                    fx.append(note(f"skip detail inv {n}: {detail}"))
            if p["failed"]:
                c["state"] = "TRIAGE"
            else:
                decide_round(c, fx)
    elif s == "TRIAGE":
        for f in p["findings"]:
            if f["class"] == "defect":
                c["queue"].append(f["inv"])
                c["files"][str(f["inv"])] = f["files"]
            else:
                fx.append(entry("dynamic", f["inv"], "skipped", f"{f['class']}: {f['evidence']}"))
        if c["queue"]:
            c["state"] = "CORRECT"
        else:
            decide_round(c, fx)
    elif s == "CORRECT":
        c["queue"].pop(0)
        c["corrected"].append(p["inv"])
        c["ever_corrected"] = sorted(set(c["ever_corrected"]) | {p["inv"]})
        if p["inv"] in c["verified"]:
            c["verified"].remove(p["inv"])
        c["acted"] += 1
        fx.append(entry("dynamic", p["inv"], "acted", f"implementation defect corrected ({p['route']})",
                        "correction", p["files"], p["fix_id"], p["regression"]))
        if p["regression"]:
            c.update(state="SUMMARY", stop="regression")
            fx.append(note(f"regression after the correction for inv {p['inv']}"))
        elif not c["queue"]:
            decide_round(c, fx)
    elif s == "SUMMARY":
        c["state"] = "DONE"
    return c, fx


SKIP_REASONS = ("app did not start", "feature flag could not be enabled", "no runtime surface to exercise")


def skip_reason(text):
    """(canonical reason, detail) for a dynamic skip. Text outside the closed set becomes 'other'."""
    t = text.strip()
    for r in SKIP_REASONS:
        if t.lower().startswith(r):
            return r, t[len(r):].strip(" :—-()")
    return "other", t


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _files(v):
    return isinstance(v, list) and bool(v) and all(isinstance(f, str) and f for f in v) \
        and not any(f.endswith(SPEC_FILES) for f in v)


def _check(p, required, optional=None):
    optional = optional or {}
    """required/optional: {key: predicate}. Unknown or missing keys and failed predicates raise."""
    unknown = set(p) - set(required) - set(optional)
    missing = set(required) - set(p)
    if unknown or missing:
        raise ValueError(f"unexpected keys {sorted(unknown)}, missing keys {sorted(missing)}")
    for k, ok in {**required, **optional}.items():
        if k in p and not ok(p[k]):
            raise ValueError(f"invalid value for '{k}'")


def _str(v):
    return isinstance(v, str) and bool(v.strip())


def _bool(v):
    return isinstance(v, bool)


def _in(*values):
    return lambda v: v in values


def normalize(ctx, p, read_report):
    """Validate `p` for ctx's state and return the payload to log. Raises ValueError on a violation.

    read_report(kind, path) -> parsed dict, or raises ValueError (the report becomes an error event).
    """
    s = ctx["state"]
    if not isinstance(p, dict):
        raise ValueError("result must be a JSON object")
    if s in TERMINAL and s != "SUMMARY":
        raise ValueError("the run is done; nothing to advance")
    if set(p) == {"error"}:
        _check(p, {"error": _str})
        return p
    if s == "INIT":
        _check(p, {"baseline": _in("green", "red", "broken")})
    elif s in ("STATIC_RUN", "DYN_RUN"):
        _check(p, {"report": _str})
        try:
            rep = read_report("static" if s == "STATIC_RUN" else "dynamic", p["report"])
        except ValueError as e:
            return {"error": str(e)}
        if s == "DYN_RUN":
            rep["skipped"] = [[n, *skip_reason(text)] for n, text in rep["skipped"]]
        return {"report": p["report"], **rep}
    elif s == "STATIC_CLASSIFY":
        _check(p, {"testable": lambda v: isinstance(v, list) and all(map(_int, v)),
                   "deferred": lambda v: isinstance(v, list) and all(
                       isinstance(d, dict) and set(d) == {"inv", "why"} and _int(d["inv"]) and _str(d["why"])
                       for d in v)})
        given = list(p["testable"]) + [d["inv"] for d in p["deferred"]]
        if sorted(given) != sorted(ctx["uncovered"]):
            raise ValueError(f"testable + deferred must be exactly the uncovered set {ctx['uncovered']}")
    elif s == "ACT_TEST":
        _check(p, {"inv": _int, "outcome": _in("already-green", "green"), "files": _files, "fix_id": _str},
               {"regression": _bool})
        p.setdefault("regression", False)
        if p["inv"] != ctx["queue"][0]:
            raise ValueError(f"expected invariant {ctx['queue'][0]}")
    elif s == "DYN_PREFLIGHT":
        if p.get("recipe") is None:
            _check(p, {"recipe": lambda v: v is None})
        else:
            _check(p, {"recipe": _str, "how": _in("existing", "chosen")}, {"why": _str})
    elif s == "RECIPE_GEN":
        if "failed" in p:
            _check(p, {"failed": _str})
        else:
            _check(p, {"recipe": _str, "route": _in("a", "b")})
    elif s == "DEP_GATE":
        _check(p, {"deps": lambda v: isinstance(v, list) and all(
            isinstance(d, dict) and set(d) == {"name", "class"} and _str(d["name"]) and d["class"] in DEP_CLASSES
            for d in v)}, {"started": _bool})
        p.setdefault("started", True)
    elif s == "TRIAGE":
        _check(p, {"findings": lambda v: isinstance(v, list) and all(
            isinstance(f, dict) and _int(f.get("inv")) and f.get("class") in TRIAGE_CLASSES and _str(f.get("evidence"))
            and set(f) <= {"inv", "class", "evidence", "files"}
            and (f["class"] != "defect" or _files(f.get("files"))) for f in v)})
        if sorted(f["inv"] for f in p["findings"]) != sorted(ctx["failed"]):
            raise ValueError(f"findings must cover exactly the failed invariants {ctx['failed']}")
    elif s == "CORRECT":
        _check(p, {"inv": _int, "files": _files, "fix_id": _str},
               {"route": _in("tdd", "fallback"), "regression": _bool})
        p.setdefault("route", "tdd")
        p.setdefault("regression", False)
        if p["inv"] != ctx["queue"][0]:
            raise ValueError(f"expected invariant {ctx['queue'][0]}")
    elif s == "SUMMARY":
        _check(p, {})
    return p


def describe(c, texts):
    """key=value pairs telling the orchestrator what to do now."""
    s = c["state"]
    d = [("state", s), ("round", c["r"]), ("closing", str(c["closing"]).lower()),
         ("action", ACTIONS[s]), ("result_schema", SCHEMAS[s])]
    if s == "STATIC_CLASSIFY":
        d.append(("uncovered", ",".join(map(str, c["uncovered"]))))
    elif s == "TRIAGE":
        d.append(("failed", ",".join(map(str, c["failed"]))))
    elif s in ("ACT_TEST", "CORRECT"):
        inv = c["queue"][0]
        d += [("invariant", inv), ("invariant_text", texts.get(inv, ""))]
        if s == "CORRECT":
            d.append(("files", ",".join(c["files"][str(inv)])))
    elif s == "SUMMARY":
        d += [("stop_reason", c["stop"] or ""), ("error", c["error"] or ""),
              ("open", ",".join(map(str, c["open"]))),
              ("unverified", ",".join(map(str, sorted(set(c["dyn_skips"]) - set(c["ever_passed"])))))]
    return d


def invariant_texts(spec_text):
    """{number: first line} for the numbered items under '## Behavior' (and its sub-headings)."""
    texts, inside = {}, False
    for line in spec_text.splitlines():
        if re.match(r"## ", line):
            inside = line.strip() == "## Behavior"
        elif inside:
            m = re.match(r"(\d+)\. (.*)$", line)
            if m:
                texts[int(m.group(1))] = m.group(2).strip()
    return texts


def event_line(ctx, payload):
    return f"- [r{ctx['r']}] event: {ctx['state']} {json.dumps(payload, sort_keys=True)}"
