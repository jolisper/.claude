LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1/static] inv 2: x — acted: added test [action: test] [files: t.py]
- [r1/dynamic] inv 5: y — acted: fixed [action: correction] [files: a.py]
- [r2/static] inv 6: z — acted: gap [action: test] [files: u.py]
"""


def test_summary_reports_tests_added_and_corrections(run_script, tmp_path):
    # Given
    log = tmp_path / "logbook.md"
    log.write_text(LOG, encoding="utf-8")

    # When
    result = run_script("auto.py", "summary", "--log", log)

    # Then
    assert result.returncode == 0, result.stderr
    parsed = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    assert parsed["status"] == "ok"
    assert parsed["tests_added"] == "2"
    assert parsed["corrections"] == "1"


SKIPPED_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1/static] inv 3: a — skipped: deferred to dynamic
- [r1/dynamic] inv 4: b — skipped: flaky run
- [r1/dynamic] inv 7: c — skipped: deferred to dynamic
"""


def test_summary_reports_skipped_count_and_reasons(run_script, tmp_path):
    # Given
    log = tmp_path / "logbook.md"
    log.write_text(SKIPPED_LOG, encoding="utf-8")

    # When
    result = run_script("auto.py", "summary", "--log", log)

    # Then
    assert result.returncode == 0, result.stderr
    parsed = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    assert parsed["status"] == "ok"
    assert parsed["tests_added"] == "0"
    assert parsed["corrections"] == "0"
    assert parsed["skipped"] == "3"
    assert parsed["skipped_by_reason"] == "deferred to dynamic:2;flaky run:1"


REGRESSION_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1/dynamic] inv 7: T — acted: R [action: correction] [files: c.py] [regression]
"""


def test_summary_reports_regression_flag(run_script, tmp_path):
    # Given
    regression_log = tmp_path / "regression.md"
    regression_log.write_text(REGRESSION_LOG, encoding="utf-8")
    clean_log = tmp_path / "clean.md"
    clean_log.write_text(LOG, encoding="utf-8")

    # When
    with_regression = run_script("auto.py", "summary", "--log", regression_log)
    without_regression = run_script("auto.py", "summary", "--log", clean_log)

    # Then
    def parse(result):
        assert result.returncode == 0, result.stderr
        return dict(
            line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
        )

    assert parse(with_regression)["regression"] == "true"
    assert parse(without_regression)["regression"] == "false"


DYNAMIC_SKIPPED_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1] note: dynamic skipped: no recipe
- [r1/static] inv 2: x — acted: added test [action: test] [files: t.py]
"""


def test_summary_reports_dynamic_skipped_with_reason(run_script, tmp_path):
    # Given
    skipped_log = tmp_path / "skipped.md"
    skipped_log.write_text(DYNAMIC_SKIPPED_LOG, encoding="utf-8")
    performed_log = tmp_path / "performed.md"
    performed_log.write_text(LOG, encoding="utf-8")

    # When
    skipped = run_script("auto.py", "summary", "--log", skipped_log)
    performed = run_script("auto.py", "summary", "--log", performed_log)

    # Then
    def parse(result):
        assert result.returncode == 0, result.stderr
        return dict(
            line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
        )

    skipped_parsed = parse(skipped)
    assert skipped_parsed["dynamic"] == "skipped"
    assert skipped_parsed["dynamic_reason"] == "no recipe"
    performed_parsed = parse(performed)
    assert performed_parsed["dynamic"] == "performed"
    assert performed_parsed["dynamic_reason"] == ""


AUTO_GENERATED_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1] note: recipe run-demo auto-generated, needs review
- [r1/static] inv 2: x — acted: added test [action: test] [files: t.py]
"""


def test_summary_reports_needs_review_for_auto_generated_recipe(run_script, tmp_path):
    # Given
    generated_log = tmp_path / "generated.md"
    generated_log.write_text(AUTO_GENERATED_LOG, encoding="utf-8")
    base_log = tmp_path / "base.md"
    base_log.write_text(LOG, encoding="utf-8")

    # When
    generated = run_script("auto.py", "summary", "--log", generated_log)
    base = run_script("auto.py", "summary", "--log", base_log)

    # Then
    def parse(result):
        assert result.returncode == 0, result.stderr
        return dict(
            line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
        )

    assert parse(generated)["needs_review"] == "true"
    assert parse(base)["needs_review"] == "false"


MULTI_RUN_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-13

Bound: up to 2 rounds
- [r1/static] inv 2: x — acted: added test [action: test] [files: t.py]

### Run 2026-11-14

Bound: up to 2 rounds
- [r1/dynamic] inv 5: y — acted: fixed [action: correction] [files: a.py]
"""


def test_summary_counts_only_latest_run_block(run_script, tmp_path):
    # Given
    log = tmp_path / "logbook.md"
    log.write_text(MULTI_RUN_LOG, encoding="utf-8")

    # When
    result = run_script("auto.py", "summary", "--log", log)

    # Then
    assert result.returncode == 0, result.stderr
    parsed = dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )
    assert parsed["tests_added"] == "0"
    assert parsed["corrections"] == "1"


NO_RUN_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Implementation files

- a.py
"""


def test_summary_without_run_block_reports_error_with_hint(run_script, tmp_path):
    # Given
    log = tmp_path / "logbook.md"
    log.write_text(NO_RUN_LOG, encoding="utf-8")

    # When
    result = run_script("auto.py", "summary", "--log", log)

    # Then
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    lines = result.stdout.splitlines()
    parsed = dict(line.split("=", 1) for line in lines if "=" in line)
    assert parsed["status"] == "error"
    assert "message" in parsed
    assert "hint" in parsed
    assert not any(line.startswith("tests_added=") for line in lines)


DELEGATED_FAILURE_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1] note: delegated-step failure: auto.py parse rejected verify-static-report.md
"""

DELEGATED_FAILURE_AFTER_DYNAMIC_LOG = DELEGATED_FAILURE_LOG + (
    "- [r1/dynamic] inv 5: y — skipped: no runtime surface\n"
)


def test_summary_reports_dynamic_not_run_when_delegated_step_failed_before_dynamic(
    run_script, tmp_path
):
    # Given a run that stopped on a delegated-step failure with no dynamic entries
    stopped = tmp_path / "stopped.md"
    stopped.write_text(DELEGATED_FAILURE_LOG, encoding="utf-8")
    # And a run with the same failure note but a dynamic-stage entry
    reached = tmp_path / "reached.md"
    reached.write_text(DELEGATED_FAILURE_AFTER_DYNAMIC_LOG, encoding="utf-8")

    # When
    stopped_result = run_script("auto.py", "summary", "--log", stopped)
    reached_result = run_script("auto.py", "summary", "--log", reached)

    # Then
    def parse(result):
        assert result.returncode == 0, result.stderr
        return dict(
            line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
        )

    stopped_parsed = parse(stopped_result)
    assert stopped_parsed["dynamic"] == "not-run"
    assert "delegated-step failure" in stopped_parsed["dynamic_reason"]
    assert parse(reached_result)["dynamic"] == "performed"


NOT_AUTO_GENERATED_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1] note: recipe run-demo chosen from existing recipes (not auto-generated)
- [r1/static] inv 2: x — acted: added test [action: test] [files: t.py]
"""


def test_summary_needs_review_false_when_note_says_not_auto_generated(run_script, tmp_path):
    # Given a note that mentions "not auto-generated"
    log = tmp_path / "logbook.md"
    log.write_text(NOT_AUTO_GENERATED_LOG, encoding="utf-8")

    # When
    result = run_script("auto.py", "summary", "--log", log)

    # Then the recipe is not flagged for review
    assert result.returncode == 0, result.stderr
    parsed = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    assert parsed["needs_review"] == "false"


SHARED_FIX_LOG = """---
spec: x
started: 2026-01-01
last-completed-phase: 8
status: complete
---

# Implementation Log: x

## Auto verification

### Run 2026-11-14

Bound: up to 2 rounds
- [r1/dynamic] inv 1: a — acted: shared defect fixed [action: correction] [files: s.ts t.ts]
- [r1/dynamic] inv 2: b — acted: shared defect fixed [action: correction] [files: s.ts t.ts]
- [r1/dynamic] inv 3: c — acted: shared defect fixed [action: correction] [files: s.ts t.ts]
- [r2/dynamic] inv 4: d — acted: other defect [action: correction] [files: u.ts]
"""


def test_summary_counts_one_correction_for_entries_sharing_reason_and_files(run_script, tmp_path):
    # Given three findings fixed by one correction and one finding fixed by another
    log = tmp_path / "logbook.md"
    log.write_text(SHARED_FIX_LOG, encoding="utf-8")

    # When
    result = run_script("auto.py", "summary", "--log", log)

    # Then corrections counts distinct fixes, not entries
    assert result.returncode == 0, result.stderr
    parsed = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    assert parsed["corrections"] == "2"
