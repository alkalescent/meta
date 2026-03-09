"""Tests for the detect module."""

from __future__ import annotations

from pathlib import Path

from meta_one.detect import detect_project_type


def test_detect_node_project(tmp_node_project: Path) -> None:
    """Test detecting Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    assert "Node" in detect_project_type(tmp_node_project).project_type


def test_detect_python_project(tmp_python_project: Path) -> None:
    """Test detecting Python project.

    Args:
        tmp_python_project (Path): Python project fixture.
    """
    assert "Python" in detect_project_type(tmp_python_project).project_type


def test_detect_rust_project(tmp_rust_project: Path) -> None:
    """Test detecting Rust project.

    Args:
        tmp_rust_project (Path): Rust project fixture.
    """
    assert "Rust" in detect_project_type(tmp_rust_project).project_type


def test_detect_empty_project(tmp_empty_project: Path) -> None:
    """Test detecting empty project.

    Args:
        tmp_empty_project (Path): Empty project fixture.
    """
    assert detect_project_type(tmp_empty_project).project_type == "Unknown"
