"""Tests for the health module."""

from __future__ import annotations

import subprocess
from pathlib import Path

from meta_one.health import run_health_checks


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)


def _commit_all(root: Path, message: str, date: str | None = None) -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    env = None
    if date:
        import os

        env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            message,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        env=env,
    )


def _statuses(checks: list, message_contains: str) -> str:
    return next(c.status for c in checks if message_contains in c.message)


def test_run_health_checks_node(tmp_node_project: Path) -> None:
    """Test running health checks on a Node.js project."""
    checks = run_health_checks(tmp_node_project)
    assert isinstance(checks, list)


def test_run_health_checks_empty(tmp_empty_project: Path) -> None:
    """Test running health checks on an empty project."""
    checks = run_health_checks(tmp_empty_project)
    assert isinstance(checks, list)


def test_health_lock_file_present(tmp_node_project: Path) -> None:
    """Test lock file detection reports ok when a lockfile exists."""
    checks = run_health_checks(tmp_node_project)
    assert _statuses(checks, "Lock file present") == "ok"


def test_health_no_lock_file(tmp_path: Path) -> None:
    """Test lock file detection warns when no lockfile exists."""
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "No lock file found") == "warn"


def test_health_missing_required_env_var(tmp_path: Path) -> None:
    """Test missing required env vars are reported as a failing check."""
    (tmp_path / ".env.example").write_text("SECRET_KEY=\n")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "missing required env vars") == "fail"


def test_health_no_missing_env_vars(tmp_path: Path) -> None:
    """Test env vars all set is reported as an ok check."""
    (tmp_path / ".env.example").write_text("SECRET_KEY=default\n")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "No missing required env vars") == "ok"


def test_health_test_files_detected(tmp_path: Path) -> None:
    """Test detecting test files reports ok."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_app.py").write_text("def test_x(): pass\n")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "Test files detected") == "ok"


def test_health_no_test_files(tmp_path: Path) -> None:
    """Test no test files present is reported as a warning."""
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "No test files detected") == "warn"


def test_health_readme_fresh(tmp_path: Path) -> None:
    """Test a recently committed README.md is reported as up to date."""
    _init_git(tmp_path)
    (tmp_path / "README.md").write_text("# App\n")
    _commit_all(tmp_path, "add readme")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "README.md is up to date") == "ok"


def test_health_readme_stale(tmp_path: Path) -> None:
    """Test an old README.md commit is reported as stale."""
    _init_git(tmp_path)
    (tmp_path / "README.md").write_text("# App\n")
    _commit_all(tmp_path, "add readme", date="2020-01-01T00:00:00")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "hasn't been updated in over 90 days") == "warn"


def test_health_readme_missing(tmp_path: Path) -> None:
    """Test a missing README.md is reported as a failing check."""
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "README.md not found") == "fail"


def test_health_readme_no_git_history(tmp_path: Path) -> None:
    """Test a README.md with no git repository can't be freshness-checked."""
    (tmp_path / "README.md").write_text("# App\n")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "Could not verify README.md freshness") == "warn"


def test_health_gitignore_present(tmp_path: Path) -> None:
    """Test .gitignore presence is reported as ok."""
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, ".gitignore present") == "ok"


def test_health_gitignore_missing(tmp_path: Path) -> None:
    """Test .gitignore absence is reported as a failing check."""
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, ".gitignore not found") == "fail"


def test_health_secrets_detected(tmp_path: Path) -> None:
    """Test a tracked file containing a secret pattern is flagged."""
    _init_git(tmp_path)
    (tmp_path / "config.py").write_text('AWS_KEY = "AKIAABCDEFGHIJKLMNOP"\n')
    _commit_all(tmp_path, "add config")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "Secrets detected in tracked files") == "fail"


def test_health_no_secrets(tmp_path: Path) -> None:
    """Test a tracked file with no secret patterns passes clean."""
    _init_git(tmp_path)
    (tmp_path / "app.py").write_text("print('hello world')\n")
    _commit_all(tmp_path, "add app")
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "No secrets detected in tracked files") == "ok"


def test_health_secret_scan_skipped_no_git(tmp_path: Path) -> None:
    """Test the secret scan is skipped gracefully when there's no git repo."""
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "Skipped secret scan") == "optional"


def test_health_ci_config_detected(tmp_path: Path) -> None:
    """Test CI configuration presence is reported as ok."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "CI configuration detected") == "ok"


def test_health_no_ci_config(tmp_path: Path) -> None:
    """Test missing CI configuration is reported as a warning."""
    checks = run_health_checks(tmp_path)
    assert _statuses(checks, "No CI configuration detected") == "warn"
