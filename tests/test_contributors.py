"""Tests for the contributors module."""

from __future__ import annotations

from pathlib import Path

from meta_one.contributors import analyze_contributors


def test_analyze_contributors_node(tmp_node_project: Path) -> None:
    """Test analyzing contributors in a Node.js project (Git init'd).

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    data = analyze_contributors(tmp_node_project)
    # Should have Alice and Bob
    assert data.contributors


def test_analyze_contributors_empty(tmp_empty_project: Path) -> None:
    """Test analyzing contributors in an empty project (no Git).

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    data = analyze_contributors(tmp_empty_project)
    assert not data.contributors
