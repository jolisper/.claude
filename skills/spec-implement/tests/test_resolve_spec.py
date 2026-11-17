def parse_kv(stdout):
    result = {}
    for line in stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            result[key] = value
    return result


def test_auto_flag_resolves_name_and_sets_auto_and_default_rounds(run_script, tmp_path):
    # Given
    initiative = tmp_path / "initiatives" / "foo"
    initiative.mkdir(parents=True)
    (initiative / "technical-spec.md").write_text("# Technical spec\n")

    # When
    result = run_script("resolve-spec.py", "--root", tmp_path, "--arg", "foo --auto")

    # Then
    assert result.returncode == 0, result.stderr
    out = parse_kv(result.stdout)
    assert out["status"] == "ok"
    assert out["name"] == "foo"
    assert out["auto"] == "true"
    assert out["rounds"] == "2"


def test_auto_flag_first_with_path_form_resolves_name_and_sets_auto(run_script, tmp_path):
    # Given
    initiative = tmp_path / "initiatives" / "foo"
    initiative.mkdir(parents=True)
    spec = initiative / "technical-spec.md"
    spec.write_text("# Technical spec\n")

    # When
    result = run_script("resolve-spec.py", "--arg", f"--auto {spec}")

    # Then
    assert result.returncode == 0, result.stderr
    out = parse_kv(result.stdout)
    assert out["status"] == "ok"
    assert out["name"] == "foo"
    assert out["auto"] == "true"
    assert out["rounds"] == "2"


def test_auto_flag_only_without_name_errors_requires_initiative_name(run_script, tmp_path):
    # Given
    # (no initiative; argument is only the --auto flag)

    # When
    result = run_script("resolve-spec.py", "--root", tmp_path, "--arg", "--auto")

    # Then
    assert result.returncode == 2
    out = parse_kv(result.stdout)
    assert out["status"] == "error"
    assert "requires an initiative name" in out["message"]


def test_without_auto_flag_sets_auto_false_and_omits_rounds(run_script, tmp_path):
    # Given
    initiative = tmp_path / "initiatives" / "foo"
    initiative.mkdir(parents=True)
    (initiative / "technical-spec.md").write_text("# Technical spec\n")

    # When
    result = run_script("resolve-spec.py", "--root", tmp_path, "--arg", "foo")

    # Then
    assert result.returncode == 0, result.stderr
    out = parse_kv(result.stdout)
    assert out["status"] == "ok"
    assert out["name"] == "foo"
    assert out["auto"] == "false"
    assert "rounds" not in out
