import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import speclog


def test_max_rounds_is_two():
    # Given the speclog library
    # When reading the MAX_ROUNDS constant
    value = speclog.MAX_ROUNDS

    # Then it equals 2
    assert value == 2


def test_format_entry_renders_skipped_decision_line():
    # Given a round, stage, invariant, text, decision and reason
    # When formatting the entry
    line = speclog.format_entry(1, 'static', 3, 'text', 'skipped', 'deferred to dynamic')

    # Then it renders the expected log line
    assert line == '- [r1/static] inv 3: text — skipped: deferred to dynamic'


def test_format_entry_appends_files_suffix_when_files_given():
    # Given a round, stage, invariant, text, decision, reason and files
    # When formatting the entry with files
    line = speclog.format_entry(2, 'dynamic', 5, 'text', 'acted', 'fixed', files=['a.py', 'b.py'])

    # Then the line ends with a files suffix
    assert line == '- [r2/dynamic] inv 5: text — acted: fixed [files: a.py, b.py]'


def test_latest_run_returns_only_last_run_block():
    # Given a body with two run blocks under an Auto verification heading
    body = (
        '## Auto verification\n'
        '\n'
        '### Run 2026-11-14\n'
        '- [r1/static] inv 1: old — skipped: old reason\n'
        '\n'
        '### Run 2026-11-15\n'
        '- [r1/static] inv 2: new — acted: new reason\n'
    )

    # When extracting the latest run
    result = speclog.latest_run(body)

    # Then only the last run block is returned
    assert result == (
        '### Run 2026-11-15\n'
        '- [r1/static] inv 2: new — acted: new reason\n'
    )
    assert 'old reason' not in result


def test_has_entry_matches_exact_round_stage_and_invariant():
    # Given a block with an inv 3 entry and another block with only inv 30
    block = (
        '### Run 2026-11-14\n'
        '- [r1/static] inv 3: text — skipped: reason\n'
    )
    block_inv_30 = (
        '### Run 2026-11-14\n'
        '- [r1/static] inv 30: text — skipped: reason\n'
    )

    # When checking for entries
    # Then it matches the exact round/stage/invariant only
    assert speclog.has_entry(block, 1, 'static', 3) is True
    assert speclog.has_entry(block, 2, 'static', 3) is False
    assert speclog.has_entry(block, 1, 'dynamic', 3) is False
    assert speclog.has_entry(block, 1, 'static', 4) is False
    assert speclog.has_entry(block_inv_30, 1, 'static', 3) is False
