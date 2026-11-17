import json

import pytest

SPEC = """# Functional spec

## Behavior

1. First behavior.
2. Second behavior.
3. Third behavior, runtime only.
4. Fourth behavior.

## Other

5. Not an invariant.
"""

LOG = (
    "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
    "# Implementation Log: x\n"
)


class Machine:
    def __init__(self, run_script, tmp_path):
        self.run_script = run_script
        self.tmp = tmp_path
        (tmp_path / "functional-spec.md").write_text(SPEC)
        self.log = tmp_path / "logbook.md"
        self.log.write_text(LOG)
        assert run_script("log.py", "auto-start", "--log", self.log, "--rounds", 2).returncode == 0

    def next(self):
        r = self.run_script("auto.py", "next", "--log", self.log)
        assert r.returncode == 0, r.stdout + r.stderr
        return kv(r.stdout)

    def advance(self, payload):
        return self.run_script("auto.py", "advance", "--log", self.log, "--result", json.dumps(payload))

    def ok(self, payload):
        r = self.advance(payload)
        assert r.returncode == 0, r.stdout + r.stderr
        return kv(r.stdout)

    def static_report(self, name, covered, uncovered):
        lines = ["# Static verify report — x", "Date: 2026-11-15", ""]
        for n in sorted(covered + uncovered):
            lines += [f"Invariant {n} — text",
                      "  Static: covered — f.py:1" if n in covered else "  Static: no coverage found", ""]
        p = self.tmp / name
        p.write_text("\n".join(lines))
        return str(p)

    def dynamic_report(self, name, passed=(), failed=(), skipped=()):
        lines = ["# Dynamic verify report — x", "Date: 2026-11-15", ""]
        for n in passed:
            lines += [f"Invariant {n} — text", "  Dynamic: pass", ""]
        for n in failed:
            lines += [f"Invariant {n} — text", "  Dynamic: fail — observed vs expected", ""]
        for n in skipped:
            lines += [f"Invariant {n} — text", "  Dynamic: skip — no runtime surface to exercise", ""]
        p = self.tmp / name
        p.write_text("\n".join(lines))
        return str(p)

    def text(self):
        return self.log.read_text()

    def to_gate(self, covered=(1, 2, 3, 4)):
        self.ok({"baseline": "green"})
        self.ok({"report": self.static_report("s.md", list(covered), [])})
        assert self.next()["state"] == "DYN_PREFLIGHT"
        self.ok({"recipe": "run-x", "how": "existing"})
        assert self.next()["state"] == "DEP_GATE"


def kv(out):
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


@pytest.fixture
def m(run_script, tmp_path):
    return Machine(run_script, tmp_path)


def test_next_on_fresh_run_starts_at_init(m):
    # When asking for the next step of a run that has only been started
    state = m.next()

    # Then it is INIT in round 1 with an action and a result schema
    assert state["state"] == "INIT"
    assert state["round"] == "1"
    assert state["action"]
    assert "baseline" in state["result_schema"]


def test_advance_baseline_green_moves_to_static_run_and_logs_event(m):
    # When the baseline is green
    m.ok({"baseline": "green"})

    # Then the next state is STATIC_RUN and the log holds one event line
    assert m.next()["state"] == "STATIC_RUN"
    events = [l for l in m.text().splitlines() if "event:" in l]
    assert events == ['- [r1] event: INIT {"baseline": "green"}']


def test_advance_rejects_unknown_key_and_leaves_log_unchanged(m):
    before = m.text()

    r = m.advance({"baseline": "green", "extra": 1})

    assert r.returncode == 2
    assert "status=error" in r.stdout
    assert m.text() == before


def test_advance_rejects_result_for_another_state(m):
    before = m.text()

    r = m.advance({"report": "x.md"})

    assert r.returncode == 2
    assert m.text() == before


def test_baseline_red_ends_run_as_failure(m):
    m.ok({"baseline": "red"})

    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "failure"
    assert "baseline red" in m.text()


def test_static_all_covered_skips_to_dynamic_preflight(m):
    m.ok({"baseline": "green"})

    m.ok({"report": m.static_report("s.md", [1, 2, 3, 4], [])})

    assert m.next()["state"] == "DYN_PREFLIGHT"


def test_static_uncovered_goes_to_classify_and_deferred_entry_uses_spec_text(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 4], [2, 3])})
    assert m.next()["state"] == "STATIC_CLASSIFY"
    assert m.next()["uncovered"] == "2,3"

    m.ok({"testable": [2], "deferred": [{"inv": 3, "why": "needs the running app"}]})

    assert "- [r1/static] inv 3: Third behavior, runtime only. — skipped: deferred to dynamic" in m.text()
    assert "- [r1] note: defer detail inv 3: needs the running app" in m.text()
    state = m.next()
    assert state["state"] == "ACT_TEST"
    assert state["invariant"] == "2"
    assert state["invariant_text"] == "Second behavior."


def test_classify_must_partition_the_uncovered_set(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 4], [2, 3])})
    before = m.text()

    r = m.advance({"testable": [2], "deferred": []})

    assert r.returncode == 2
    assert m.text() == before


def test_act_test_rejects_spec_file_in_files(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 3, 4], [2])})
    m.ok({"testable": [2], "deferred": []})
    before = m.text()

    r = m.advance({"inv": 2, "outcome": "already-green", "files": ["initiatives/x/functional-spec.md"],
                   "fix_id": "t1"})

    assert r.returncode == 2
    assert m.text() == before


def test_act_test_regression_stops_the_run_and_flags_the_entry(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 3, 4], [2])})
    m.ok({"testable": [2], "deferred": []})

    m.ok({"inv": 2, "outcome": "green", "files": ["a.py"], "fix_id": "t1", "regression": True})

    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "regression"
    assert "- [r1/static] inv 2: Second behavior. — acted: coverage-gap test (green) [action: test] [fix: t1] [files: a.py] [regression]" in m.text()


def test_no_recipe_generates_once_then_skips_dynamic_in_later_rounds(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 3, 4], [2])})
    m.ok({"testable": [2], "deferred": []})
    m.ok({"inv": 2, "outcome": "already-green", "files": ["t.py"], "fix_id": "t1"})
    assert m.next()["state"] == "DYN_PREFLIGHT"

    m.ok({"recipe": None})
    assert m.next()["state"] == "RECIPE_GEN"
    m.ok({"failed": "app would not start"})

    # dynamic skipped and the round decides: acted, so round 2 starts
    assert "dynamic skipped: no recipe could be generated: app would not start" in m.text()
    state = m.next()
    assert state["state"] == "STATIC_RUN"
    assert state["round"] == "2"

    # round 2 with everything covered: preflight is skipped, no second generation
    m.ok({"report": m.static_report("s2.md", [1, 2, 3, 4], [])})
    assert m.next()["state"] == "SUMMARY"
    assert m.text().count("RECIPE_GEN") == 1


def test_generated_recipe_is_flagged_and_proceeds_to_gate(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 2, 3, 4], [])})
    m.ok({"recipe": None})

    m.ok({"recipe": "run-x", "route": "b"})

    assert "recipe run-x auto-generated, needs review (route: b)" in m.text()
    assert m.next()["state"] == "DEP_GATE"


def test_production_dependency_stops_before_any_dynamic_run(m):
    m.to_gate()

    m.ok({"deps": [{"name": "db", "class": "local"}, {"name": "api", "class": "production"}]})

    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "safety"
    assert "safety stop: blocked on api" in m.text()
    assert m.advance({"report": "x.md"}).returncode == 2


def test_unknown_dependency_class_is_rejected(m):
    m.to_gate()

    r = m.advance({"deps": [{"name": "db", "class": "staging"}]})

    assert r.returncode == 2


def test_clean_first_round_ends_with_summary_and_no_actions(m):
    m.to_gate()
    m.ok({"deps": [{"name": "db", "class": "local"}]})
    assert m.next()["state"] == "DYN_RUN"

    m.ok({"report": m.dynamic_report("d.md", passed=[1, 2, 3, 4])})

    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "clean"
    assert state["tests_added"] == "0"
    assert state["corrections"] == "0"
    assert state["dynamic"] == "performed"


def test_dynamic_skips_are_logged_with_their_reason(m):
    m.to_gate()
    m.ok({"deps": []})

    m.ok({"report": m.dynamic_report("d.md", passed=[1, 2, 4], skipped=[3])})

    assert "- [r1/dynamic] inv 3: Third behavior, runtime only. — skipped: no runtime surface to exercise" in m.text()


def test_free_text_skip_reasons_collapse_to_a_closed_set(m):
    m.to_gate()
    m.ok({"deps": []})
    report = m.dynamic_report("d.md", passed=[1, 2], skipped=[3, 4])
    body = open(report).read()
    body = body.replace("skip — no runtime surface to exercise", "skip — not exercised (no process was spawned)", 1)
    body = body.replace("skip — no runtime surface to exercise", "skip — no runtime surface to exercise (internal only)", 1)
    open(report, "w").write(body)

    m.ok({"report": report})

    log = m.text()
    assert "inv 3: Third behavior, runtime only. — skipped: other" in log
    assert "note: skip detail inv 3: not exercised (no process was spawned)" in log
    assert "inv 4: Fourth behavior. — skipped: no runtime surface to exercise" in log
    assert "note: skip detail inv 4: internal only" in log


def test_failures_must_all_be_triaged_and_defects_are_corrected(m):
    m.to_gate()
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d.md", passed=[1, 4], failed=[2, 3])})
    assert m.next()["state"] == "TRIAGE"
    assert m.next()["failed"] == "2,3"

    # a partial triage is rejected
    assert m.advance({"findings": [{"inv": 2, "class": "defect", "evidence": "e", "files": ["a.py"]}]}).returncode == 2

    m.ok({"findings": [
        {"inv": 2, "class": "defect", "evidence": "returns 1, expected 2", "files": ["a.py"]},
        {"inv": 3, "class": "flaky", "evidence": "passed on re-run"},
    ]})

    assert "- [r1/dynamic] inv 3: Third behavior, runtime only. — skipped: flaky: passed on re-run" in m.text()
    state = m.next()
    assert state["state"] == "CORRECT"
    assert state["invariant"] == "2"
    assert state["files"] == "a.py"

    m.ok({"inv": 2, "route": "tdd", "files": ["a.py", "a.test.py"], "fix_id": "f1"})

    assert "- [r1/dynamic] inv 2: Second behavior. — acted: implementation defect corrected (tdd) [action: correction] [fix: f1] [files: a.py, a.test.py]" in m.text()
    # a correction forces a static re-run before the next dynamic run
    state = m.next()
    assert state["state"] == "STATIC_RUN"
    assert state["round"] == "2"


def test_non_defect_triage_never_reaches_correct(m):
    m.to_gate()
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d.md", passed=[1, 2, 4], failed=[3])})

    m.ok({"findings": [{"inv": 3, "class": "spec-mismatch", "evidence": "spec says 5, app says 6"}]})

    # nothing acted and the open set is unchanged from "no previous": no progress
    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "no-progress"
    assert state["open"] == "3"


def test_acts_in_the_last_round_trigger_a_closing_verify_without_actions(m):
    # round 1: a correction
    m.to_gate()
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d1.md", passed=[1, 3, 4], failed=[2])})
    m.ok({"findings": [{"inv": 2, "class": "defect", "evidence": "e", "files": ["a.py"]}]})
    m.ok({"inv": 2, "files": ["a.py"], "fix_id": "f1"})
    # round 2: static clean, dynamic fails again, second correction
    m.ok({"report": m.static_report("s2.md", [1, 2, 3, 4], [])})
    assert m.next()["state"] == "DEP_GATE"
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d2.md", passed=[1, 3, 4], failed=[2])})
    m.ok({"findings": [{"inv": 2, "class": "defect", "evidence": "e2", "files": ["a.py"]}]})
    m.ok({"inv": 2, "files": ["a.py"], "fix_id": "f2"})

    # bound reached with acts: closing verify, static then gate then dynamic
    state = m.next()
    assert state["state"] == "STATIC_RUN"
    assert state["closing"] == "true"
    m.ok({"report": m.static_report("s3.md", [1, 2, 3, 4], [])})
    assert m.next()["state"] == "DEP_GATE"
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d3.md", passed=[1, 3, 4], failed=[2])})

    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "bound"
    assert state["open"] == "2"
    assert state["corrections"] == "2"
    assert m.advance({}).returncode == 0
    assert m.next()["state"] == "DONE"


def test_deferred_invariant_that_passed_dynamically_is_not_deferred_again(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s1.md", [1, 4], [2, 3])})
    m.ok({"testable": [2], "deferred": [{"inv": 3, "why": "needs the running app"}]})
    m.ok({"inv": 2, "outcome": "green", "files": ["a.test.py"], "fix_id": "t2"})
    m.ok({"recipe": "run-x", "how": "existing"})
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d1.md", passed=[1, 3, 4], skipped=[2])})
    # round 2: static still has 3 uncovered, and the dynamic run skips it this time
    m.ok({"report": m.static_report("s2.md", [1, 2, 4], [3])})
    m.ok({"testable": [], "deferred": [{"inv": 3, "why": "needs the running app, again"}]})
    m.ok({"deps": []})

    m.ok({"report": m.dynamic_report("d2.md", passed=[1, 2, 4], skipped=[3])})

    state = m.next()
    assert state["stop_reason"] == "clean"
    assert state["open"] == ""
    assert state["unverified"] == ""
    assert m.text().count("inv 3: Third behavior, runtime only. — skipped: deferred to dynamic") == 1


def test_summary_lists_invariants_that_were_never_verified_dynamically(m):
    m.to_gate()
    m.ok({"deps": []})

    m.ok({"report": m.dynamic_report("d.md", passed=[1, 2], skipped=[3, 4])})

    state = m.next()
    assert state["stop_reason"] == "clean"
    assert state["unverified"] == "3,4"


def test_correction_is_logged_as_verified_once_it_passes_again(m):
    m.to_gate()
    m.ok({"deps": []})
    m.ok({"report": m.dynamic_report("d1.md", passed=[1, 3, 4], failed=[2])})
    m.ok({"findings": [{"inv": 2, "class": "defect", "evidence": "e", "files": ["a.py"]}]})
    m.ok({"inv": 2, "files": ["a.py"], "fix_id": "f1"})
    m.ok({"report": m.static_report("s2.md", [1, 2, 3, 4], [])})
    m.ok({"deps": []})

    m.ok({"report": m.dynamic_report("d2.md", passed=[1, 2, 3, 4])})

    assert "- [r2/dynamic] inv 2: Second behavior. — verified: re-verified after correction: pass" in m.text()
    assert m.text().count("re-verified after correction") == 1


def test_error_result_ends_the_run_as_a_delegated_failure(m):
    m.ok({"baseline": "green"})

    m.ok({"error": "agent asked a question"})

    state = m.next()
    assert state["state"] == "SUMMARY"
    assert state["stop_reason"] == "failure"
    assert state["error"] == "agent asked a question"
    assert state["dynamic"] == "not-run"
    assert "- [r1] note: delegated-step failure: agent asked a question" in m.text()


def test_unparseable_static_report_ends_the_run_as_a_failure(m):
    m.ok({"baseline": "green"})
    bad = m.tmp / "bad.md"
    bad.write_text("Invariant 1 — a\n  Static: maybe\n")

    m.ok({"report": str(bad)})

    state = m.next()
    assert state["stop_reason"] == "failure"
    assert "unrecognized static verdict" in state["error"]


def test_state_is_rebuilt_from_the_log_alone(m):
    m.ok({"baseline": "green"})
    m.ok({"report": m.static_report("s.md", [1, 3, 4], [2])})

    # a fresh process (every call is one) sees the same state; the log is the only memory
    assert m.next()["state"] == "STATIC_CLASSIFY"
    assert m.next()["state"] == "STATIC_CLASSIFY"
