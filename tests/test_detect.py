"""Tests for the detect module."""

from __future__ import annotations

import json
from pathlib import Path

from meta_one.detect import (
    _detect_node_framework,
    _detect_python_framework,
    detect_all_project_types,
    detect_project_type,
)


def test_detect_node_project(tmp_node_project: Path) -> None:
    """Test detecting Node.js project.

    Args:
        tmp_node_project (Path): Node.js project fixture.
    """
    info = detect_project_type(tmp_node_project)
    assert "Node" in info.project_type
    assert info.language == "TypeScript"
    assert info.framework == "Next.js"


def test_detect_python_project(tmp_python_project: Path) -> None:
    """Test detecting Python project.

    Args:
        tmp_python_project (Path): Python project fixture.
    """
    info = detect_project_type(tmp_python_project)
    assert "Python" in info.project_type
    assert info.framework == "FastAPI"


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


def test_detect_node_framework_no_package_json(tmp_path: Path) -> None:
    """Test node framework detection with no package.json present."""
    assert _detect_node_framework(tmp_path) == ""


def test_detect_node_framework_malformed_package_json(tmp_path: Path) -> None:
    """Test node framework detection tolerates malformed package.json."""
    (tmp_path / "package.json").write_text("not json")
    assert _detect_node_framework(tmp_path) == ""


def test_detect_node_no_typescript(tmp_path: Path) -> None:
    """Test Node.js project without tsconfig.json is detected as JavaScript."""
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))
    info = detect_project_type(tmp_path)
    assert info.language == "JavaScript"


def test_detect_python_framework_no_pyproject(tmp_path: Path) -> None:
    """Test Python framework detection with no pyproject.toml present."""
    assert _detect_python_framework(tmp_path) == ""


def test_detect_dotnet_csproj(tmp_path: Path) -> None:
    """Test detecting a .NET project via a .csproj file."""
    (tmp_path / "App.csproj").write_text("<Project />")
    info = detect_project_type(tmp_path)
    assert info.project_type == ".NET"
    assert info.marker_file == "App.csproj"


def test_detect_dotnet_sln_only(tmp_path: Path) -> None:
    """Test detecting a .NET project via a .sln file with no .csproj."""
    (tmp_path / "App.sln").write_text("Microsoft Visual Studio Solution File")
    info = detect_project_type(tmp_path)
    assert info.project_type == ".NET"
    assert info.marker_file == "App.sln"


def test_detect_all_project_types(tmp_python_project: Path) -> None:
    """Test detecting all project types, including a .NET marker alongside others."""
    (tmp_python_project / "App.csproj").write_text("<Project />")
    infos = detect_all_project_types(tmp_python_project)
    types = {info.project_type for info in infos}
    assert "Python" in types
    assert ".NET" in types


def test_detect_all_project_types_empty(tmp_empty_project: Path) -> None:
    """Test detecting all project types in an empty project returns nothing."""
    assert detect_all_project_types(tmp_empty_project) == []
