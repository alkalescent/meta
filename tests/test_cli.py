"""Tests for the CLI commands."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from meta_one.cli import app
from meta_one.deps import Dependency, DepsResult, OutdatedDependency
from meta_one.health import HealthCheck
from meta_one.size import DirStats, FileStats, LanguageStats, SizeResult

runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


def test_help_command() -> None:
    """Test help flag shows usage information."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "deps" in result.stdout
    assert "scripts" in result.stdout
    assert "env" in result.stdout
    assert "size" in result.stdout
    assert "contributors" in result.stdout
    assert "health" in result.stdout
    assert "version" in result.stdout


def test_version_command() -> None:
    """Test version command outputs version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("v")


def test_version_flag() -> None:
    """Test --version flag outputs version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("v")


def test_version_short_flag() -> None:
    """Test -v short flag outputs version."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("v")


def test_json_version() -> None:
    """Test --json version command."""
    result = runner.invoke(app, ["--json", "version"])
    assert result.exit_code == 0
    assert '"version"' in result.stdout


# --- overview ---


def test_overview_text(tmp_node_project: Path) -> None:
    """Test bare invocation prints a text overview."""
    result = runner.invoke(app, ["--path", str(tmp_node_project)])
    assert result.exit_code == 0
    assert "Project:" in result.stdout
    assert "Language:" in result.stdout
    assert "Health:" in result.stdout


def test_overview_json(tmp_node_project: Path) -> None:
    """Test bare invocation with --json prints structured overview data."""
    result = runner.invoke(app, ["--json", "--path", str(tmp_node_project)])
    assert result.exit_code == 0
    assert '"project"' in result.stdout
    assert '"health_issues"' in result.stdout
    assert "Not fully implemented" not in result.stdout


def test_overview_git_failure(tmp_empty_project: Path) -> None:
    """Test overview tolerates a target with no git repo."""
    result = runner.invoke(app, ["--path", str(tmp_empty_project)])
    assert result.exit_code == 0
    assert "unknown" in result.stdout


def test_overview_git_not_installed(tmp_empty_project: Path) -> None:
    """Test overview survives git being absent from PATH.

    FileNotFoundError is an OSError rather than a SubprocessError, so catching
    only the latter used to surface a traceback to the user.
    """
    with patch(
        "meta_one.cli.subprocess.check_output", side_effect=FileNotFoundError("git")
    ):
        result = runner.invoke(app, ["--path", str(tmp_empty_project)])
    assert result.exit_code == 0
    assert result.exception is None
    assert "unknown" in result.stdout


def test_overview_shows_framework(tmp_path: Path) -> None:
    """Test a detected framework is shown alongside the project type."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\ndependencies = ["fastapi"]\n'
    )
    result = runner.invoke(app, ["--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "Type:        Python (FastAPI)" in result.stdout


def test_overview_json_includes_framework(tmp_path: Path) -> None:
    """Test the framework is present in JSON overview output."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\ndependencies = ["flask"]\n'
    )
    result = runner.invoke(app, ["--json", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["framework"] == "Flask"


# --- deps ---


def test_deps_command() -> None:
    """Test deps command runs without error."""
    with patch("meta_one.cli.analyze_deps") as mock_analyze:
        mock_analyze.return_value = DepsResult(
            production=[Dependency("react", "18.0.0", False)],
            dev=[Dependency("eslint", "8.0.0", True)],
            ecosystem="Node.js",
        )
        result = runner.invoke(app, ["deps"])
        assert result.exit_code == 0
        assert "Production Dependencies" in result.stdout
        assert "Development Dependencies" in result.stdout


def test_deps_dev_only() -> None:
    """Test deps --dev shows only development dependencies."""
    with patch("meta_one.cli.analyze_deps") as mock_analyze:
        mock_analyze.return_value = DepsResult(
            production=[Dependency("react", "18.0.0", False)],
            dev=[Dependency("eslint", "8.0.0", True)],
            ecosystem="Node.js",
        )
        result = runner.invoke(app, ["deps", "--dev"])
        assert result.exit_code == 0
        assert "Development Dependencies" in result.stdout
        assert "Production Dependencies" not in result.stdout
        assert "react" not in result.stdout


def test_deps_quiet() -> None:
    """Test deps --quiet prints only a summary count."""
    with patch("meta_one.cli.analyze_deps") as mock_analyze:
        mock_analyze.return_value = DepsResult(
            production=[Dependency("react", "18.0.0", False)],
            dev=[Dependency("eslint", "8.0.0", True)],
            ecosystem="Node.js",
        )
        result = runner.invoke(app, ["--quiet", "deps"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "1 dependencies, 1 dev"


def test_deps_json_dev_only() -> None:
    """Test deps --json --dev only includes dev deps in the payload."""
    with patch("meta_one.cli.analyze_deps") as mock_analyze:
        mock_analyze.return_value = DepsResult(
            production=[Dependency("react", "18.0.0", False)],
            dev=[Dependency("eslint", "8.0.0", True)],
            ecosystem="Node.js",
        )
        result = runner.invoke(app, ["--json", "deps", "--dev"])
        assert result.exit_code == 0
        assert '"production"' not in result.stdout
        assert '"eslint"' in result.stdout


def test_deps_outdated_with_results() -> None:
    """Test deps --outdated renders an outdated table."""
    with (
        patch("meta_one.cli.analyze_deps") as mock_analyze,
        patch("meta_one.cli.check_outdated") as mock_check,
    ):
        mock_analyze.return_value = DepsResult(
            production=[Dependency("react", "17.0.0", False)],
            dev=[],
            ecosystem="Node.js",
        )
        mock_check.return_value = (
            [OutdatedDependency("react", "17.0.0", "18.0.0")],
            None,
        )
        result = runner.invoke(app, ["deps", "--outdated"])
        assert result.exit_code == 0
        assert "Outdated:" in result.stdout
        assert "18.0.0" in result.stdout


def test_deps_outdated_up_to_date() -> None:
    """Test deps --outdated reports when nothing is outdated."""
    with (
        patch("meta_one.cli.analyze_deps") as mock_analyze,
        patch("meta_one.cli.check_outdated") as mock_check,
    ):
        mock_analyze.return_value = DepsResult(
            production=[], dev=[], ecosystem="Node.js"
        )
        mock_check.return_value = ([], None)
        result = runner.invoke(app, ["deps", "--outdated"])
        assert result.exit_code == 0
        assert "All dependencies up to date." in result.stdout


def test_deps_outdated_note() -> None:
    """Test deps --outdated surfaces a note for unsupported ecosystems."""
    with (
        patch("meta_one.cli.analyze_deps") as mock_analyze,
        patch("meta_one.cli.check_outdated") as mock_check,
    ):
        mock_analyze.return_value = DepsResult(production=[], dev=[], ecosystem="Ruby")
        mock_check.return_value = (
            [],
            "Outdated check not supported for Ruby projects.",
        )
        result = runner.invoke(app, ["deps", "--outdated"])
        assert result.exit_code == 0
        assert "not supported" in result.stdout


def test_deps_outdated_json() -> None:
    """Test deps --json --outdated includes the outdated payload."""
    with (
        patch("meta_one.cli.analyze_deps") as mock_analyze,
        patch("meta_one.cli.check_outdated") as mock_check,
    ):
        mock_analyze.return_value = DepsResult(
            production=[], dev=[], ecosystem="Node.js"
        )
        mock_check.return_value = (
            [OutdatedDependency("react", "17.0.0", "18.0.0")],
            "a note",
        )
        result = runner.invoke(app, ["--json", "deps", "--outdated"])
        assert result.exit_code == 0
        assert '"outdated"' in result.stdout
        assert '"outdated_note"' in result.stdout


# --- scripts ---


def test_scripts_command() -> None:
    """Test scripts command lists discovered scripts as a table."""
    with patch("meta_one.cli.discover_scripts") as mock_discover:
        from meta_one.scripts import Script, ScriptSource

        mock_discover.return_value = [
            ScriptSource(
                "package.json", [Script("build", "next build", "production build")]
            )
        ]
        result = runner.invoke(app, ["scripts"])
        assert result.exit_code == 0
        assert "build" in result.stdout
        assert "next build" in result.stdout


def test_scripts_quiet() -> None:
    """Test scripts --quiet prints only a summary count."""
    with patch("meta_one.cli.discover_scripts") as mock_discover:
        from meta_one.scripts import Script, ScriptSource

        mock_discover.return_value = [
            ScriptSource(
                "package.json", [Script("build", "next build", "production build")]
            )
        ]
        result = runner.invoke(app, ["--quiet", "scripts"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "1 scripts discovered"


def test_scripts_run_success(tmp_node_project: Path) -> None:
    """Test scripts --run executes the resolved script command."""
    fake_result = subprocess.CompletedProcess(args=[], returncode=0)
    with patch("meta_one.cli.subprocess.run", return_value=fake_result) as mock_run:
        result = runner.invoke(
            app, ["--path", str(tmp_node_project), "scripts", "--run", "build"]
        )
        assert result.exit_code == 0
        mock_run.assert_called_once()
        assert mock_run.call_args.kwargs["shell"] is True


def test_scripts_run_not_found(tmp_node_project: Path) -> None:
    """Test scripts --run reports an error for an unknown script name."""
    result = runner.invoke(
        app, ["--path", str(tmp_node_project), "scripts", "--run", "does-not-exist"]
    )
    assert result.exit_code == 1
    assert "No script named" in result.output


# --- env ---


def test_env_command(tmp_node_project: Path) -> None:
    """Test env command renders a table of expected variables."""
    result = runner.invoke(app, ["--path", str(tmp_node_project), "env"])
    assert result.exit_code == 0
    assert "DATABASE_URL" in result.stdout


def test_env_quiet(tmp_node_project: Path) -> None:
    """Test env --quiet prints only a summary count."""
    result = runner.invoke(app, ["--quiet", "--path", str(tmp_node_project), "env"])
    assert result.exit_code == 0
    assert "expected" in result.stdout
    assert "missing" in result.stdout


def test_env_json(tmp_node_project: Path) -> None:
    """Test env --json outputs structured variable data."""
    result = runner.invoke(app, ["--json", "--path", str(tmp_node_project), "env"])
    assert result.exit_code == 0
    assert '"variables"' in result.stdout


# --- size ---


def test_size_command() -> None:
    """Test size command renders language/directory/largest-file sections."""
    with patch("meta_one.cli.analyze_size") as mock_analyze:
        mock_analyze.return_value = SizeResult(
            languages=[LanguageStats("Python", 2, 100, 500, 100.0)],
            directories=[DirStats("src", 2, 100, 500)],
            largest_files=[FileStats("src/app.py", 80, 400)],
            total_files=2,
            total_lines=100,
            total_bytes=500,
        )
        result = runner.invoke(app, ["size"])
        assert result.exit_code == 0
        assert "Languages:" in result.stdout
        assert "Python" in result.stdout
        assert "Directories:" in result.stdout
        assert "Largest Files:" in result.stdout


def test_size_quiet() -> None:
    """Test size --quiet suppresses the breakdown sections."""
    with patch("meta_one.cli.analyze_size") as mock_analyze:
        mock_analyze.return_value = SizeResult(
            languages=[LanguageStats("Python", 2, 100, 500, 100.0)],
            directories=[],
            largest_files=[],
            total_files=2,
            total_lines=100,
            total_bytes=500,
        )
        result = runner.invoke(app, ["--quiet", "size"])
        assert result.exit_code == 0
        assert "Languages:" not in result.stdout
        assert "Total:" in result.stdout


def test_size_json() -> None:
    """Test size --json includes the full breakdown."""
    with patch("meta_one.cli.analyze_size") as mock_analyze:
        mock_analyze.return_value = SizeResult(
            languages=[LanguageStats("Python", 2, 100, 500, 100.0)],
            directories=[DirStats("src", 2, 100, 500)],
            largest_files=[FileStats("src/app.py", 80, 400)],
            total_files=2,
            total_lines=100,
            total_bytes=500,
        )
        result = runner.invoke(app, ["--json", "size"])
        assert result.exit_code == 0
        assert '"languages"' in result.stdout
        assert '"total_bytes"' in result.stdout


def test_size_sort_bytes() -> None:
    """Test size --sort bytes is passed through to the analyzer."""
    with patch("meta_one.cli.analyze_size") as mock_analyze:
        mock_analyze.return_value = SizeResult(
            languages=[],
            directories=[],
            largest_files=[],
            total_files=0,
            total_lines=0,
            total_bytes=0,
        )
        result = runner.invoke(app, ["size", "--sort", "bytes"])
        assert result.exit_code == 0
        assert mock_analyze.call_args.kwargs["sort_by"] == "bytes"


# --- contributors ---


def test_contributors_command() -> None:
    """Test contributors command renders a table."""
    with patch("meta_one.cli.analyze_contributors") as mock_analyze:
        from meta_one.contributors import Contributor, ContributorsResult

        mock_analyze.return_value = ContributorsResult(
            contributors=[Contributor("Alice", 5, 10, 2, "2 days ago")],
            recent_files=[],
            churn_hotspots=[],
        )
        result = runner.invoke(app, ["contributors"])
        assert result.exit_code == 0
        assert "Alice" in result.stdout
        assert "5 commits" in result.stdout


def test_contributors_shows_recent_files_and_churn() -> None:
    """Test the recent-files and churn data the analyzer computes is displayed."""
    with patch("meta_one.cli.analyze_contributors") as mock_analyze:
        from meta_one.contributors import (
            ChurnFile,
            Contributor,
            ContributorsResult,
            RecentFile,
        )

        mock_analyze.return_value = ContributorsResult(
            contributors=[Contributor("Alice", 5, 10, 2, "2 days ago")],
            recent_files=[RecentFile("src/app.py", 4, 2)],
            churn_hotspots=[ChurnFile("src/legacy.py", 42)],
        )
        result = runner.invoke(app, ["contributors"])
        assert result.exit_code == 0
        assert "Recently Active Files" in result.stdout
        assert "src/app.py" in result.stdout
        assert "2 authors" in result.stdout
        assert "Churn Hotspots" in result.stdout
        assert "src/legacy.py" in result.stdout
        assert "42 commits" in result.stdout


def test_contributors_json_includes_recent_and_churn() -> None:
    """Test JSON output carries the recent-files and churn sections."""
    with patch("meta_one.cli.analyze_contributors") as mock_analyze:
        from meta_one.contributors import (
            ChurnFile,
            Contributor,
            ContributorsResult,
            RecentFile,
        )

        mock_analyze.return_value = ContributorsResult(
            contributors=[Contributor("Alice", 5, 10, 2, "2 days ago")],
            recent_files=[RecentFile("src/app.py", 4, 2)],
            churn_hotspots=[ChurnFile("src/legacy.py", 42)],
        )
        result = runner.invoke(app, ["--json", "contributors"])
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["recent_files"][0]["path"] == "src/app.py"
        assert payload["churn_hotspots"][0]["commits"] == 42


def test_contributors_quiet() -> None:
    """Test contributors --quiet prints only a summary count."""
    with patch("meta_one.cli.analyze_contributors") as mock_analyze:
        from meta_one.contributors import Contributor, ContributorsResult

        mock_analyze.return_value = ContributorsResult(
            contributors=[Contributor("Alice", 5, 10, 2, "2 days ago")],
            recent_files=[],
            churn_hotspots=[],
        )
        result = runner.invoke(app, ["--quiet", "contributors"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "1 contributors"


def test_health_symbols_colored_when_supported() -> None:
    """Test health symbols carry color when the terminal supports it."""
    with (
        patch("meta_one.cli.run_health_checks") as mock_checks,
        patch("meta_one.output._supports_color", return_value=True),
    ):
        mock_checks.return_value = [
            HealthCheck("ok", "Lock file present"),
            HealthCheck("optional", "No environment example file found"),
            HealthCheck("fail", "README.md not found"),
        ]
        # color=True keeps click from stripping ANSI on a non-tty stream.
        result = runner.invoke(app, ["health"], color=True)
        assert result.exit_code == 0
        assert "\033[32m" in result.stdout
        assert "\033[31m" in result.stdout
        assert "○" in result.stdout


def test_health_symbols_plain_with_no_color() -> None:
    """Test --no-color suppresses color even where the terminal supports it."""
    with (
        patch("meta_one.cli.run_health_checks") as mock_checks,
        patch("meta_one.output._supports_color", return_value=True),
    ):
        mock_checks.return_value = [HealthCheck("ok", "Lock file present")]
        result = runner.invoke(app, ["--no-color", "health"], color=True)
        assert result.exit_code == 0
        assert "\033[" not in result.stdout
        assert "✓" in result.stdout


def test_contributors_since_author_flags() -> None:
    """Test contributors passes --since/--author through to the analyzer."""
    with patch("meta_one.cli.analyze_contributors") as mock_analyze:
        from meta_one.contributors import ContributorsResult

        mock_analyze.return_value = ContributorsResult(
            contributors=[], recent_files=[], churn_hotspots=[]
        )
        result = runner.invoke(
            app, ["contributors", "--since", "30 days ago", "--author", "Alice"]
        )
        assert result.exit_code == 0
        mock_analyze.assert_called_once()
        assert mock_analyze.call_args.kwargs["since"] == "30 days ago"
        assert mock_analyze.call_args.kwargs["author"] == "Alice"


# --- health ---


def test_health_command() -> None:
    """Test health command renders correct status symbols."""
    with patch("meta_one.cli.run_health_checks") as mock_run:
        mock_run.return_value = [
            HealthCheck("ok", "Lock file present"),
            HealthCheck("warn", "No CI configuration detected"),
            HealthCheck("fail", "README.md not found"),
            HealthCheck("optional", "No environment example file found"),
        ]
        result = runner.invoke(app, ["health"])
        assert result.exit_code == 0
        assert "✓" in result.stdout
        assert "⚠" in result.stdout
        assert "✗" in result.stdout


def test_health_quiet_filters_ok() -> None:
    """Test health --quiet only prints failing/warning checks."""
    with patch("meta_one.cli.run_health_checks") as mock_run:
        mock_run.return_value = [
            HealthCheck("ok", "Lock file present"),
            HealthCheck("fail", "README.md not found"),
        ]
        result = runner.invoke(app, ["--quiet", "health"])
        assert result.exit_code == 0
        assert "Lock file present" not in result.stdout
        assert "README.md not found" in result.stdout


def test_health_json() -> None:
    """Test health --json outputs structured check data."""
    with patch("meta_one.cli.run_health_checks") as mock_run:
        mock_run.return_value = [HealthCheck("ok", "Lock file present")]
        result = runner.invoke(app, ["--json", "health"])
        assert result.exit_code == 0
        assert '"status": "ok"' in result.stdout
