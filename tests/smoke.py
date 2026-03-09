"""Smoke tests for the meta_one CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_package_name() -> str:
    """Get the package name from pyproject.toml.

    Returns:
        str: Package name.
    """
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return "meta_one"

    for line in pyproject.read_text().splitlines():
        if line.startswith("name = "):
            return line.split("=")[1].strip().strip('"').strip("'")
    return "meta_one"


def test_imports() -> None:
    """Test importing modules."""
    import meta_one
    import meta_one.cli
    import meta_one.detect
    import meta_one.output

    assert meta_one is not None
    assert meta_one.cli.app is not None
    assert meta_one.detect is not None
    assert meta_one.output is not None


def test_cli_help() -> None:
    """Test CLI help output via subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "meta_one.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "deps" in result.stdout
    assert "scripts" in result.stdout
    assert "env" in result.stdout
    assert "size" in result.stdout
    assert "contributors" in result.stdout
    assert "health" in result.stdout


def test_cli_version() -> None:
    """Test CLI version output via subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "meta_one.cli", "version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_size() -> None:
    """Test CLI size output via subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "meta_one.cli", "size"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_health() -> None:
    """Test CLI health output via subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "meta_one.cli", "health"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
