import datetime


def test_auto_start_appends_auto_verification_section_preserving_original(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)

    # When
    result = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)

    # Then
    assert result.returncode == 0, result.stderr
    assert "status=ok" in result.stdout
    content = log.read_text()
    assert content.startswith(original)
    appended = content[len(original):]
    today = datetime.date.today().isoformat()
    lines = appended.splitlines()
    i1 = lines.index("## Auto verification")
    i2 = lines.index(f"### Run {today}")
    i3 = next(i for i, l in enumerate(lines) if "Bound: up to 2 rounds" in l)
    assert i1 < i2 < i3


def test_auto_start_twice_appends_second_run_without_rewriting_earlier_entries(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)

    # When
    first = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    after_first = log.read_text()
    second = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    after_second = log.read_text()

    # Then
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    lines = after_second.splitlines()
    assert lines.count("## Auto verification") == 1
    assert len([l for l in lines if l.startswith("### Run ")]) == 2
    assert after_second.startswith(after_first)


def test_auto_entry_appends_formatted_skipped_line_preserving_prior_content(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr
    before = log.read_text()

    # When
    result = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "static",
        "--invariant", 3, "--text", "T", "--decision", "skipped",
        "--action", "none", "--reason", "deferred to dynamic",
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "status=ok" in result.stdout
    after = log.read_text()
    assert after.startswith(before)
    last = [l for l in after.splitlines() if l.strip()][-1]
    assert last == "- [r1/static] inv 3: T — skipped: deferred to dynamic"


def test_auto_entry_identical_repeat_reports_unchanged_and_leaves_file_byte_identical(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr
    args = (
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "static",
        "--invariant", 3, "--text", "T", "--decision", "skipped",
        "--action", "none", "--reason", "deferred to dynamic",
    )
    first = run_script(*args)
    after_first = log.read_bytes()

    # When
    second = run_script(*args)
    after_second = log.read_bytes()

    # Then
    assert first.returncode == 0, first.stderr
    assert "status=ok" in first.stdout
    assert second.returncode == 0, second.stderr
    assert "status=unchanged" in second.stdout
    assert after_second == after_first


def test_auto_entry_new_round_appends_line_and_preserves_earlier_round_entry(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr

    def entry(round_no):
        return run_script(
            "log.py", "auto-entry", "--log", log, "--round", round_no, "--stage", "static",
            "--invariant", 3, "--text", "T", "--decision", "skipped",
            "--action", "none", "--reason", "deferred to dynamic",
        )

    first = entry(1)
    after_first = log.read_text()

    # When
    second = entry(2)

    # Then
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert "status=ok" in second.stdout
    after_second = log.read_text()
    new_line = "- [r2/static] inv 3: T — skipped: deferred to dynamic"
    assert after_second.startswith(after_first)
    assert after_second.rstrip("\n").splitlines()[-1] == new_line
    lines = after_second.splitlines()
    assert len([l for l in lines if l.startswith("- [r1/static] inv 3:")]) == 1


def test_auto_entry_with_files_appends_files_suffix_to_line(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr

    # When
    result = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "static",
        "--invariant", 5, "--text", "T", "--decision", "acted",
        "--action", "none", "--reason", "R", "--files", "a.py", "b.py",
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "status=ok" in result.stdout
    last = [l for l in log.read_text().splitlines() if l.strip()][-1]
    assert last == "- [r1/static] inv 5: T — acted: R [files: a.py, b.py]"


def test_auto_entry_with_action_appends_action_suffix_before_files_suffix(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr

    # When
    result = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "static",
        "--invariant", 6, "--text", "T", "--decision", "acted",
        "--action", "test", "--reason", "R", "--files", "t.py",
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "status=ok" in result.stdout
    last = [l for l in log.read_text().splitlines() if l.strip()][-1]
    assert last == "- [r1/static] inv 6: T — acted: R [action: test] [files: t.py]"


def test_auto_entry_with_regression_flag_appends_regression_suffix_last(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr

    # When
    result = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "dynamic",
        "--invariant", 7, "--text", "T", "--decision", "acted",
        "--action", "correction", "--reason", "R", "--files", "c.py", "--regression",
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "status=ok" in result.stdout
    last = [l for l in log.read_text().splitlines() if l.strip()][-1]
    assert last == "- [r1/dynamic] inv 7: T — acted: R [action: correction] [files: c.py] [regression]"


def test_auto_entry_without_prior_auto_start_reports_clean_error_and_leaves_file_unchanged(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)

    # When
    result = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "static",
        "--invariant", 3, "--text", "T", "--decision", "skipped",
        "--action", "none", "--reason", "R",
    )

    # Then
    assert result.returncode == 2, result.stderr
    assert "status=error" in result.stdout
    lines = result.stdout.splitlines()
    assert any(l.startswith("message=") for l in lines)
    assert any(l.startswith("hint=") for l in lines)
    assert "Traceback" not in result.stderr
    assert log.read_text() == original


def test_auto_note_appends_formatted_note_line_preserving_prior_content(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    started = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)
    assert started.returncode == 0, started.stderr
    before = log.read_bytes()

    # When
    result = run_script(
        "log.py", "auto-note", "--log", log, "--round", 1,
        "--text", "dynamic skipped: no recipe",
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert "status=ok" in result.stdout
    after = log.read_bytes()
    assert after.startswith(before)
    last = [l for l in after.decode().splitlines() if l.strip()][-1]
    assert last == "- [r1] note: dynamic skipped: no recipe"


def test_auto_note_without_prior_auto_start_reports_clean_error_and_leaves_file_unchanged(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)

    # When
    result = run_script("log.py", "auto-note", "--log", log, "--round", 1, "--text", "N")

    # Then
    assert result.returncode == 2, result.stderr
    assert "status=error" in result.stdout
    lines = result.stdout.splitlines()
    assert any(l.startswith("message=") for l in lines)
    assert any(l.startswith("hint=") for l in lines)
    assert log.read_text() == original


def test_status_after_auto_commands_still_reports_session_log_with_untouched_frontmatter(run_script, tmp_path):
    # Given
    original = (
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n\n## Implementation files\n\n- a.py\n"
    )
    log = tmp_path / "log.md"
    log.write_text(original)
    assert run_script("log.py", "auto-start", "--log", log, "--rounds", 2).returncode == 0
    entry = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "static",
        "--invariant", 3, "--text", "T", "--decision", "skipped",
        "--action", "none", "--reason", "R",
    )
    assert entry.returncode == 0, entry.stderr
    note = run_script("log.py", "auto-note", "--log", log, "--round", 1, "--text", "N")
    assert note.returncode == 0, note.stderr

    # When
    result = run_script("log.py", "status", "--log", log)

    # Then
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "status=ok" in lines
    assert "kind=session" in lines
    assert "last_completed=8" in lines


def test_auto_start_rejects_logbook_without_last_completed_phase(run_script, tmp_path):
    # Given
    original = "---\nstatus: draft\nstarted: 2026-01-01\n---\n\n# Initiative\n"
    log = tmp_path / "log.md"
    log.write_text(original)

    # When
    result = run_script("log.py", "auto-start", "--log", log, "--rounds", 2)

    # Then
    assert result.returncode == 2, result.stderr
    assert "status=error" in result.stdout
    assert any(l.startswith("message=") for l in result.stdout.splitlines())
    assert log.read_text() == original


def test_auto_entry_rejects_placeholder_invariant_text_and_leaves_file_unchanged(run_script, tmp_path):
    # Given a closed log after auto-start
    log = tmp_path / "log.md"
    log.write_text(
        "---\nspec: x\nstarted: 2026-01-01\nlast-completed-phase: 8\nstatus: complete\n---\n\n"
        "# Implementation Log: x\n"
    )
    assert run_script("log.py", "auto-start", "--log", log, "--rounds", 2).returncode == 0
    before = log.read_text()

    # When the entry text is a placeholder instead of the invariant text
    result = run_script(
        "log.py", "auto-entry", "--log", log, "--round", 1, "--stage", "dynamic",
        "--invariant", 6, "--text", "invariant 6 (see functional-spec)",
        "--decision", "acted", "--action", "correction", "--reason", "R",
    )

    # Then it exits 2 with a clean error and the file is unchanged
    assert result.returncode == 2
    assert "status=error" in result.stdout
    assert "placeholder" in result.stdout
    assert log.read_text() == before
