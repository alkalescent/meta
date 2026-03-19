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


def test_discover_scripts_makefile(tmp_path: Path) -> None:
    """Test discovering scripts from a Makefile, skipping private targets."""
    (tmp_path / "Makefile").write_text(
        "build:\n\techo build\ntest:\n\techo test\n_hidden:\n\techo hidden\n.PHONY: build test\n"
    )
    scripts = discover_scripts(tmp_path)
    source = next(s for s in scripts if s.source_file == "Makefile")
    names = [s.name for s in source.scripts]
    assert "build" in names
    assert "test" in names
    assert "_hidden" not in names
    build_script = next(s for s in source.scripts if s.name == "build")
    assert build_script.command == "make build"
    assert build_script.description == "run make target"


def test_discover_scripts_justfile(tmp_path: Path) -> None:
    """Test discovering scripts from a justfile."""
    (tmp_path / "justfile").write_text(
        "build:\n\techo build\n_helper:\n\techo helper\n"
    )
    scripts = discover_scripts(tmp_path)
    source = next(s for s in scripts if s.source_file == "justfile")
    names = [s.name for s in source.scripts]
    assert "build" in names
    assert "_helper" not in names
    assert source.scripts[0].command == "just build"


def test_discover_scripts_taskfile(tmp_path: Path) -> None:
    """Test discovering scripts from a Taskfile.yml."""
    (tmp_path / "Taskfile.yml").write_text(
        "version: '3'\ntasks:\n  build:\n    cmds:\n      - echo build\n  test:\n    cmds:\n      - echo test\n"
    )
    scripts = discover_scripts(tmp_path)
    source = next(s for s in scripts if s.source_file == "Taskfile.yml")
    names = [s.name for s in source.scripts]
    assert names == ["build", "test"]
    assert source.scripts[0].command == "task build"


def test_discover_scripts_pyproject_taskipy(tmp_path: Path) -> None:
    """Test discovering scripts from pyproject.toml's taskipy tasks."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.taskipy.tasks]\ntest = "pytest"\nlint = "ruff check ."\n'
    )
    scripts = discover_scripts(tmp_path)
    source = next(s for s in scripts if s.source_file == "pyproject.toml")
    names = {s.name: s.description for s in source.scripts}
    assert names["test"] == "run tests"
    assert names["lint"] == "lint codebase"


def test_discover_scripts_pyproject_project_scripts(tmp_path: Path) -> None:
    """Test discovering scripts from pyproject.toml's [project.scripts]."""
    (tmp_path / "pyproject.toml").write_text(
        '[project.scripts]\nmeta = "meta_one.cli:app"\n'
    )
    scripts = discover_scripts(tmp_path)
    source = next(s for s in scripts if s.source_file == "pyproject.toml")
    assert source.scripts[0].name == "meta"


def test_discover_scripts_malformed_package_json(tmp_path: Path) -> None:
    """Test package.json discovery tolerates malformed JSON."""
    (tmp_path / "package.json").write_text("not json")
    scripts = discover_scripts(tmp_path)
    assert scripts == []


def test_discover_scripts_malformed_pyproject(tmp_path: Path) -> None:
    """Test pyproject.toml discovery tolerates malformed TOML."""
    (tmp_path / "pyproject.toml").write_text("not [ valid")
    scripts = discover_scripts(tmp_path)
    assert scripts == []


def test_discover_scripts_taskfile_no_tasks(tmp_path: Path) -> None:
    """Test Taskfile.yml discovery when there is no tasks: section."""
    (tmp_path / "Taskfile.yml").write_text("version: '3'\n")
    scripts = discover_scripts(tmp_path)
    assert scripts == []


def test_infer_description_fallback() -> None:
    """Test description inference falls back to a generic label."""
    from meta_one.scripts import _infer_description

    assert _infer_description("some-unknown-command --flag") == "run script"
