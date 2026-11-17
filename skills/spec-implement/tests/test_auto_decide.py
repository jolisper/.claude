def parse_kv(stdout):
    return dict(
        line.split("=", 1) for line in stdout.splitlines() if "=" in line
    )


def test_decide_continues_when_invariants_remain_open(run_script):
    # Given round 1, two actions taken, invariants 3 and 4 still open
    # When decide is invoked
    result = run_script(
        "auto.py", "decide", "--round", "1", "--acted", "2", "--open", "3,4"
    )

    # Then it exits 0 and reports status=continue
    assert result.returncode == 0, result.stderr
    assert parse_kv(result.stdout)["status"] == "continue"


def test_decide_stops_clean_when_nothing_open(run_script):
    # Given round 1, no actions taken, nothing open
    # When decide is invoked
    result = run_script(
        "auto.py", "decide", "--round", "1", "--acted", "0", "--open", ""
    )

    # Then it exits 0 and reports status=stop with reason=clean
    assert result.returncode == 0, result.stderr
    kv = parse_kv(result.stdout)
    assert kv["status"] == "stop"
    assert kv["reason"] == "clean"


def test_decide_stops_no_progress_when_nothing_acted_and_invariant_open(run_script):
    # Given round 1, no actions taken, invariant 3 still open, no --prev-open
    # When decide is invoked
    result = run_script(
        "auto.py", "decide", "--round", "1", "--acted", "0", "--open", "3"
    )

    # Then it exits 0 and reports status=stop with reason=no-progress
    assert result.returncode == 0, result.stderr
    kv = parse_kv(result.stdout)
    assert kv["status"] == "stop"
    assert kv["reason"] == "no-progress"


def test_decide_continues_when_nothing_acted_but_open_set_changed(run_script):
    # Given round 1, nothing acted, open set {3} differs from previous {3,4}
    # When decide is invoked
    result = run_script(
        "auto.py", "decide", "--round", "1", "--acted", "0",
        "--open", "3", "--prev-open", "3,4",
    )

    # Then it exits 0 and reports status=continue
    assert result.returncode == 0, result.stderr
    assert parse_kv(result.stdout)["status"] == "continue"


def test_decide_stops_bound_when_last_round_acted_and_invariant_still_open(run_script):
    # Given round 2 (MAX_ROUNDS), one action taken, invariant 3 still open
    # When decide is invoked
    result = run_script(
        "auto.py", "decide", "--round", "2", "--acted", "1",
        "--open", "3", "--prev-open", "3,4",
    )

    # Then it exits 0 and reports status=stop with reason=bound
    assert result.returncode == 0, result.stderr
    kv = parse_kv(result.stdout)
    assert kv["status"] == "stop"
    assert kv["reason"] == "bound"


def test_decide_stops_no_progress_not_bound_on_last_round_when_open_set_unchanged(run_script):
    # Given round 2 (last round), nothing acted, open set equal to previous
    # (including a differently ordered representation)
    for open_arg, prev_arg in (("3", "3"), ("4,3", "3,4")):
        # When decide is invoked
        result = run_script(
            "auto.py", "decide", "--round", "2", "--acted", "0",
            "--open", open_arg, "--prev-open", prev_arg,
        )

        # Then it exits 0 and reports status=stop with reason=no-progress
        assert result.returncode == 0, result.stderr
        kv = parse_kv(result.stdout)
        assert kv["status"] == "stop"
        assert kv["reason"] == "no-progress"
