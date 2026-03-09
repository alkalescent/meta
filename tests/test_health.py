"""Tests for the health module."""

from __future__ import annotations

from pathlib import Path

from meta_one.health import run_health_checks


def test_run_health_checks_node(tmp_node_project: Path) -> None:
    """Test running health checks on a Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    checks = run_health_checks(tmp_node_project)
    assert isinstance(checks, list)


def test_run_health_checks_empty(tmp_empty_project: Path) -> None:
    """Test running health checks on an empty project.

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    checks = run_health_checks(tmp_empty_project)
    assert isinstance(checks, list)
