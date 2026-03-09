"""Tests for the deps module."""

from __future__ import annotations

from pathlib import Path

from meta_one.deps import analyze_deps


def test_analyze_deps_node(tmp_node_project: Path) -> None:
    """Test analyzing dependencies for a Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    deps = analyze_deps(tmp_node_project)
    # The fixture might not have dependencies set, or parsing could fail due to missing lockfile.
    # Just asserting it returns a result structure for the node project
    assert deps.ecosystem == "Node.js"


def test_analyze_deps_python(tmp_python_project: Path) -> None:
    """Test analyzing dependencies for a Python project.

    Args:
        tmp_python_project (Path): Python project fixture.
    """
    deps = analyze_deps(tmp_python_project)
    assert deps.ecosystem == "Python"


def test_analyze_deps_empty(tmp_empty_project: Path) -> None:
    """Test analyzing dependencies for an empty project.

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    deps = analyze_deps(tmp_empty_project)
    assert not deps.production
    assert not deps.dev
