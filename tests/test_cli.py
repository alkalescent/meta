"""Tests for the CLI commands."""

from unittest.mock import patch

from typer.testing import CliRunner

from meta_one.cli import app

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


def test_deps_command() -> None:
    """Test deps command runs without error."""
    # Using mock since we don't have a real project here
    with patch("meta_one.cli.analyze_deps") as mock_analyze:
        from meta_one.deps import DepsResult

        mock_analyze.return_value = DepsResult(
            production=[], dev=[], ecosystem="Node.js"
        )
        result = runner.invoke(app, ["deps"])
        assert result.exit_code == 0


def test_health_command() -> None:
    """Test health command runs without error."""
    with patch("meta_one.cli.run_health_checks") as mock_run:
        mock_run.return_value = []
        result = runner.invoke(app, ["health"])
        assert result.exit_code == 0


def test_size_command() -> None:
    """Test size command runs without error."""
    with patch("meta_one.cli.analyze_size") as mock_analyze:
        from meta_one.size import SizeResult

        mock_analyze.return_value = SizeResult(
            languages=[], directories=[], largest_files=[], total_files=0, total_lines=0
        )
        result = runner.invoke(app, ["size"])
        assert result.exit_code == 0


def test_json_version() -> None:
    """Test --json version command."""
    result = runner.invoke(app, ["--json", "version"])
    assert result.exit_code == 0
    # The output might be plain text or JSON depending on implementation,
    # but it shouldn't error.
