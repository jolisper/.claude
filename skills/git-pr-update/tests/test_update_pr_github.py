import os
import stat
import subprocess

import pytest


@pytest.fixture
def mock_gh(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "auth" ]; then exit 0; fi\n'
        'if [ "$1" = "pr" ] && [ "$2" = "edit" ]; then\n'
        '  echo "https://github.com/myorg/myrepo/pull/42"\n'
        "  exit 0\n"
        "fi\n"
        "exit 1\n"
    )
    fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{bin_dir}:{os.environ.get('PATH', '')}"


@pytest.fixture
def mock_gh_unauthenticated(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "auth" ]; then exit 1; fi\n'
        "exit 1\n"
    )
    fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{bin_dir}:{os.environ.get('PATH', '')}"


@pytest.fixture
def mock_gh_edit_fails(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "auth" ]; then exit 0; fi\n'
        'if [ "$1" = "pr" ] && [ "$2" = "edit" ]; then\n'
        '  echo "pull request not found" >&2\n'
        "  exit 1\n"
        "fi\n"
        "exit 1\n"
    )
    fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{bin_dir}:{os.environ.get('PATH', '')}"


def test_help_exits_zero_and_lists_all_flags():
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"

    # When
    result = subprocess.run(
        ["bash", script, "--help"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    # Then
    assert result.returncode == 0
    assert "--repo" in output
    assert "--pr-id" in output
    assert "--title" in output
    assert "--description-file" in output


def test_missing_repo_flag_exits_one_and_prints_required():
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"

    # When
    result = subprocess.run(
        ["bash", script, "--pr-id", "1", "--title", "t", "--description-file", "/tmp/x"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    # Then
    assert result.returncode == 1
    assert "required" in result.stderr


def test_missing_pr_id_and_other_flags_exits_one_and_prints_required():
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"

    # When
    result = subprocess.run(
        ["bash", script, "--repo", "myorg/myrepo"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    # Then
    assert result.returncode == 1
    assert "required" in result.stderr


def test_description_file_not_found_exits_one_and_prints_not_found():
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--repo", "myorg/myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", "/tmp/nonexistent_file_that_does_not_exist_xyz",
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    # Then
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_gh_unauthenticated_last_stdout_line_is_status_unauthorized(mock_gh_unauthenticated, tmp_path):
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"
    desc_file = tmp_path / "desc.txt"
    desc_file.write_text("My PR description")
    env = {k: v for k, v in os.environ.items()}
    env["PATH"] = mock_gh_unauthenticated

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--repo", "myorg/myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", str(desc_file),
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )

    # Then
    assert result.returncode == 0
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line == "status=unauthorized"


def test_gh_edit_failure_last_stdout_line_is_status_error(mock_gh_edit_fails, tmp_path):
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"
    desc_file = tmp_path / "desc.txt"
    desc_file.write_text("My PR description")
    env = {k: v for k, v in os.environ.items()}
    env["PATH"] = mock_gh_edit_fails

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--repo", "myorg/myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", str(desc_file),
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )

    # Then
    assert result.returncode == 0
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line == "status=error"
    assert "pull request not found" in result.stderr


def test_successful_update_exits_zero_and_last_stdout_line_is_status_updated(mock_gh, tmp_path):
    # Given
    script = "skills/git-pr-update/scripts/update-pr-github.sh"
    cwd = "/Users/jorge.perez/.claude"
    desc_file = tmp_path / "desc.txt"
    desc_file.write_text("My PR description")
    env = {k: v for k, v in os.environ.items()}
    env["PATH"] = mock_gh

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--repo", "myorg/myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", str(desc_file),
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )

    # Then
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert lines[-1] == "status=updated"
    assert lines[0] == "https://github.com/myorg/myrepo/pull/42"
