import os
import stat
import subprocess
import tempfile

import pytest


@pytest.fixture
def mock_curl(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_curl = bin_dir / "curl"
    fake_curl.write_text(
        '#!/bin/sh\nprintf \'{"id": 42, "title": "Updated PR"}\'\nprintf "\\n200\\n"\n'
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{bin_dir}:{os.environ.get('PATH', '')}"


def test_help_exits_zero_and_lists_all_flags():
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
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
    assert "--workspace" in output
    assert "--repo" in output
    assert "--pr-id" in output
    assert "--title" in output
    assert "--description-file" in output


def test_missing_workspace_flag_exits_one_and_prints_required():
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"

    # When
    result = subprocess.run(
        ["bash", script, "--repo", "myrepo", "--pr-id", "1", "--title", "t", "--description-file", "/tmp/x"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    # Then
    assert result.returncode == 1
    assert "required" in result.stderr


def test_missing_repo_and_other_flags_exits_one_and_prints_required():
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"

    # When
    result = subprocess.run(
        ["bash", script, "--workspace", "myws"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    # Then
    assert result.returncode == 1
    assert "required" in result.stderr


def test_missing_bitbucket_token_env_exits_one_and_prints_token_name():
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"
    env_without_token = {k: v for k, v in os.environ.items() if k != "BITBUCKET_TOKEN"}

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"some description")
        desc_file = f.name

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--workspace", "myws",
            "--repo", "myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", desc_file,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env_without_token,
    )

    # Then
    assert result.returncode == 1
    assert "BITBUCKET_TOKEN" in result.stderr


def test_missing_bitbucket_username_env_exits_one_and_prints_username_name():
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"
    env_with_token_no_username = {k: v for k, v in os.environ.items() if k != "BITBUCKET_USERNAME"}
    env_with_token_no_username["BITBUCKET_TOKEN"] = "fake-token"

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"some description")
        desc_file = f.name

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--workspace", "myws",
            "--repo", "myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", desc_file,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env_with_token_no_username,
    )

    # Then
    assert result.returncode == 1
    assert "BITBUCKET_USERNAME" in result.stderr


def test_description_file_not_found_exits_one_and_prints_not_found():
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"
    env = {k: v for k, v in os.environ.items()}
    env["BITBUCKET_TOKEN"] = "fake-token"
    env["BITBUCKET_USERNAME"] = "fake-user"

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--workspace", "myws",
            "--repo", "myrepo",
            "--pr-id", "42",
            "--title", "My PR",
            "--description-file", "/tmp/nonexistent_file_that_does_not_exist_xyz",
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )

    # Then
    assert result.returncode == 1
    assert "not found" in result.stderr


@pytest.fixture
def mock_curl_401(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_curl = bin_dir / "curl"
    fake_curl.write_text(
        '#!/bin/sh\nprintf \'{"error": "unauthorized"}\'\nprintf "\\n401\\n"\n'
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{bin_dir}:{os.environ.get('PATH', '')}"


def test_http_401_response_last_stdout_line_is_status_unauthorized(mock_curl_401, tmp_path):
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"
    desc_file = tmp_path / "desc.txt"
    desc_file.write_text("My PR description")
    env = {k: v for k, v in os.environ.items()}
    env["BITBUCKET_TOKEN"] = "tok"
    env["BITBUCKET_USERNAME"] = "user"
    env["PATH"] = mock_curl_401

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--workspace", "myws",
            "--repo", "myrepo",
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
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line == "status=unauthorized"


@pytest.fixture
def mock_curl_403(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_curl = bin_dir / "curl"
    fake_curl.write_text(
        '#!/bin/sh\nprintf \'{"error": "forbidden"}\'\nprintf "\\n403\\n"\n'
    )
    fake_curl.chmod(fake_curl.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return f"{bin_dir}:{os.environ.get('PATH', '')}"


def test_http_403_response_last_stdout_line_is_status_forbidden(mock_curl_403, tmp_path):
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"
    desc_file = tmp_path / "desc.txt"
    desc_file.write_text("My PR description")
    env = {k: v for k, v in os.environ.items()}
    env["BITBUCKET_TOKEN"] = "tok"
    env["BITBUCKET_USERNAME"] = "user"
    env["PATH"] = mock_curl_403

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--workspace", "myws",
            "--repo", "myrepo",
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
    last_line = result.stdout.strip().splitlines()[-1]
    assert last_line == "status=forbidden"


def test_successful_update_exits_zero_and_last_stdout_line_is_status_updated(mock_curl, tmp_path):
    # Given
    script = "skills/git-pr-update/scripts/update-pr.sh"
    cwd = "/Users/jorge.perez/.claude"
    desc_file = tmp_path / "desc.txt"
    desc_file.write_text("My PR description")
    env = {k: v for k, v in os.environ.items()}
    env["BITBUCKET_TOKEN"] = "tok"
    env["BITBUCKET_USERNAME"] = "user"
    env["PATH"] = mock_curl

    # When
    result = subprocess.run(
        [
            "bash", script,
            "--workspace", "myws",
            "--repo", "myrepo",
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
    assert last_line == "status=updated"
