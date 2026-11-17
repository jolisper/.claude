import pytest


REPORT = """# Static verify report — demo
Date: 2026-11-14

Invariant 1 — a
  Static: covered — f.py:3

Invariant 2 — b
  Static: no coverage found

Invariant 3 — c
  Static: covered — g.py:9

3 invariants — 2 covered, 1 uncovered
"""


def test_parse_static_report_lists_covered_and_uncovered(run_script, tmp_path):
    # Given a static verify report with 2 covered and 1 uncovered invariant
    report = tmp_path / "static-report.md"
    report.write_text(REPORT, encoding="utf-8")

    # When parsing it with kind static
    result = run_script("auto.py", "parse", "--kind", "static", "--report", report)

    # Then it exits 0 and prints the key=value summary
    assert result.returncode == 0, result.stderr
    parsed = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    assert parsed["status"] == "ok"
    assert parsed["total"] == "3"
    assert parsed["covered"] == "1,3"
    assert parsed["uncovered"] == "2"


UNRECOGNIZED_STATIC_REPORT = """# Static verify report — demo
Date: 2026-11-14

Invariant 1 — a
  Static: covered — f.py:3

Invariant 2 — b
  Static: maybe

2 invariants — 1 covered, 1 uncovered
"""


def test_parse_static_report_with_unrecognized_verdict_fails_closed(
    run_script, tmp_path
):
    # Given a static report where invariant 2 has an unrecognized verdict
    report = tmp_path / "static-report.md"
    report.write_text(UNRECOGNIZED_STATIC_REPORT, encoding="utf-8")

    # When parsing it with kind static
    result = run_script("auto.py", "parse", "--kind", "static", "--report", report)

    # Then it exits 2 with an error, message naming invariant 2 and a hint,
    # and does not guess covered/uncovered
    assert result.returncode == 2, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    parsed = dict(line.split("=", 1) for line in lines if "=" in line)
    assert parsed["status"] == "error"
    assert "2" in parsed["message"]
    assert "hint" in parsed
    assert not any(line.startswith(("covered=", "uncovered=")) for line in lines)


DYNAMIC_REPORT = """# Dynamic verify report — demo
Date: 2026-11-14

Invariant 1 — a
  Dynamic: pass

Invariant 2 — b
  Dynamic: fail — got 500 expected 200

Invariant 3 — c
  Dynamic: skip — app did not start

Invariant 4 — d
  Dynamic: skip — no runtime surface to exercise

4 invariants — 1 passed, 1 failed, 2 skipped
"""


def test_parse_dynamic_report_lists_passed_failed_skipped_with_reasons(
    run_script, tmp_path
):
    # Given a dynamic verify report with pass, fail and two skipped invariants
    report = tmp_path / "dynamic-report.md"
    report.write_text(DYNAMIC_REPORT, encoding="utf-8")

    # When parsing it with kind dynamic
    result = run_script("auto.py", "parse", "--kind", "dynamic", "--report", report)

    # Then it exits 0 and prints the key=value summary
    assert result.returncode == 0, result.stderr
    parsed = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    assert parsed["status"] == "ok"
    assert parsed["total"] == "4"
    assert parsed["passed"] == "1"
    assert parsed["failed"] == "2"
    assert parsed["skipped"] == "3,4"
    assert parsed["skip_reasons"] == (
        "3:app did not start;4:no runtime surface to exercise"
    )


EMPTY_REPORT_TEMPLATE = """# {title} verify report — demo
Date: 2026-11-14

0 invariants — 0 covered, 0 uncovered
"""


@pytest.mark.parametrize("kind", ["static", "dynamic"])
def test_parse_report_without_invariants_fails_closed(run_script, tmp_path, kind):
    # Given a report with a title and date but no Invariant blocks
    report = tmp_path / f"{kind}-report.md"
    report.write_text(
        EMPTY_REPORT_TEMPLATE.format(title=kind.capitalize()), encoding="utf-8"
    )

    # When parsing it
    result = run_script("auto.py", "parse", "--kind", kind, "--report", report)

    # Then it exits 2 with a "no invariants" error and a hint, no total
    assert result.returncode == 2, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    parsed = dict(line.split("=", 1) for line in lines if "=" in line)
    assert parsed["status"] == "error"
    assert "no invariants" in parsed["message"]
    assert "hint" in parsed
    assert not any(line.startswith("total=") for line in lines)
    assert "Traceback" not in result.stderr


MALFORMED_DYNAMIC_TEMPLATE = """# Dynamic verify report — demo
Date: 2026-11-14

Invariant 1 — a
  Dynamic: pass

Invariant 2 — b
  Dynamic: fail — x

Invariant 3 — c
{verdict_line}

3 invariants
"""


@pytest.mark.parametrize("verdict_line", ["  Dynamic: skip", "  Dynamic: maybe"])
def test_parse_dynamic_report_with_malformed_verdict_fails_closed(
    run_script, tmp_path, verdict_line
):
    # Given a dynamic report where invariant 3 has a bare skip or unknown verdict
    report = tmp_path / "dynamic-report.md"
    report.write_text(
        MALFORMED_DYNAMIC_TEMPLATE.format(verdict_line=verdict_line),
        encoding="utf-8",
    )

    # When parsing it with kind dynamic
    result = run_script("auto.py", "parse", "--kind", "dynamic", "--report", report)

    # Then it exits 2 with an error naming invariant 3 and a hint, no counts
    assert result.returncode == 2, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    parsed = dict(line.split("=", 1) for line in lines if "=" in line)
    assert parsed["status"] == "error"
    assert "3" in parsed["message"]
    assert "hint" in parsed
    assert not any(
        line.startswith(("passed=", "failed=", "skipped=")) for line in lines
    )


TRAILING_TEXT_STATIC_REPORT = """# Static verify report — demo
Date: 2026-11-14

Invariant 1 — a
  Static: covered — f.py:3

Invariant 2 — b
  Static: no coverage found — nothing exercises files/ persistence

2 invariants — 1 covered, 1 uncovered
"""


def test_parse_static_report_accepts_explanation_after_no_coverage_found(run_script, tmp_path):
    # Given a static report whose uncovered verdict carries a trailing explanation
    report = tmp_path / "static-report.md"
    report.write_text(TRAILING_TEXT_STATIC_REPORT, encoding="utf-8")

    # When parsing it with kind static
    result = run_script("auto.py", "parse", "--kind", "static", "--report", report)

    # Then invariant 2 is uncovered and the report is not rejected
    assert result.returncode == 0, result.stderr
    parsed = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    assert parsed["covered"] == "1"
    assert parsed["uncovered"] == "2"
