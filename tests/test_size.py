"""Tests for the size module."""

from __future__ import annotations

from pathlib import Path

from meta_one.size import analyze_size


def test_analyze_size_node(tmp_node_project: Path) -> None:
    """Test analyzing size of a Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    data = analyze_size(tmp_node_project)
    assert data.total_lines >= 0
    assert data.total_files >= 0


def test_analyze_size_empty(tmp_empty_project: Path) -> None:
    """Test analyzing size of an empty project.

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    data = analyze_size(tmp_empty_project)
    assert data.total_files == 0
    assert data.total_lines == 0
