"""Tests for the env module."""

from __future__ import annotations

from pathlib import Path

from meta_one.env import analyze_env


def test_analyze_env_node(tmp_node_project: Path) -> None:
    """Test analyzing env variables in a Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    data = analyze_env(tmp_node_project)
    assert data.expected_vars
    _ = [v.name for v in data.expected_vars]


def test_analyze_env_empty(tmp_empty_project: Path) -> None:
    """Test analyzing env variables in an empty project.

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    data = analyze_env(tmp_empty_project)
    assert not data.expected_vars
