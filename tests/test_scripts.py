"""Tests for the scripts module."""

from __future__ import annotations

from pathlib import Path

from meta_one.scripts import discover_scripts


def test_discover_scripts_node(tmp_node_project: Path) -> None:
    """Test discovering scripts in a Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    scripts = discover_scripts(tmp_node_project)
    names = [s.name for source in scripts for s in source.scripts]

    assert "dev" in names
    assert "build" in names
    assert "test" in names
    assert "lint" in names


def test_discover_scripts_empty(tmp_empty_project: Path) -> None:
    """Test discovering scripts in an empty project.

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    scripts = discover_scripts(tmp_empty_project)
    assert len(scripts) == 0
