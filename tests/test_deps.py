"""Tests for the deps module."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from meta_one.deps import (
    Dependency,
    DepsResult,
    _dev_dependency_names,
    _is_outdated,
    _normalize_pkg_name,
    analyze_deps,
    check_outdated,
)

# A uv.lock with a root project entry, so the graph walk applies. "shared" is
# reachable from both roots and must stay in production.
_UV_LOCK_WITH_ROOT = """
version = 1

[[package]]
name = "app"
source = { editable = "." }
dependencies = [{ name = "fastapi" }]

[package.dev-dependencies]
dev = [{ name = "pytest" }]

[package.metadata]
requires-dist = [{ name = "fastapi" }]

[[package]]
name = "fastapi"
version = "0.100.0"
dependencies = [{ name = "starlette" }, { name = "shared" }]

[[package]]
name = "starlette"
version = "0.27.0"

[[package]]
name = "pytest"
version = "7.4.0"
dependencies = [{ name = "pluggy" }, { name = "shared" }]

[[package]]
name = "pluggy"
version = "1.3.0"

[[package]]
name = "shared"
version = "1.0.0"
"""


def test_analyze_deps_node(tmp_node_project: Path) -> None:
    """Test analyzing dependencies for a Node.js project."""
    deps = analyze_deps(tmp_node_project)
    assert deps.ecosystem == "Node.js"


def test_analyze_deps_python(tmp_python_project: Path) -> None:
    """Test analyzing dependencies for a Python project."""
    deps = analyze_deps(tmp_python_project)
    assert deps.ecosystem == "Python"


def test_analyze_deps_empty(tmp_empty_project: Path) -> None:
    """Test analyzing dependencies for an empty project."""
    deps = analyze_deps(tmp_empty_project)
    assert not deps.production
    assert not deps.dev
    assert deps.ecosystem == "unknown"


def test_normalize_pkg_name() -> None:
    """Test PEP 503 package name normalization."""
    assert _normalize_pkg_name("My_Package.Name") == "my-package-name"
    assert _normalize_pkg_name("ruff") == "ruff"


def test_dev_dependency_names_missing_file(tmp_path: Path) -> None:
    """Test dev dependency extraction when pyproject.toml is absent."""
    assert _dev_dependency_names(tmp_path / "pyproject.toml") == set()


def test_dev_dependency_names_malformed(tmp_path: Path) -> None:
    """Test dev dependency extraction with malformed TOML."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("not [ valid toml")
    assert _dev_dependency_names(pyproject) == set()


def test_dev_dependency_names_parses_versions(tmp_path: Path) -> None:
    """Test dev dependency names are extracted without version specifiers."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[dependency-groups]\ndev = ["pytest>=7.0", "Ruff"]\n')
    assert _dev_dependency_names(pyproject) == {"pytest", "ruff"}


# --- Node.js ---


def test_parse_nodejs_package_lock_packages_format(tmp_path: Path) -> None:
    """Test parsing package-lock.json v3 'packages' format."""
    (tmp_path / "package.json").write_text(json.dumps({"name": "app"}))
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "packages": {
                    "": {
                        "dependencies": {"react": "18.0.0"},
                        "devDependencies": {"eslint": "8.0.0"},
                    }
                }
            }
        )
    )
    deps = analyze_deps(tmp_path)
    assert deps.production == [Dependency("react", "18.0.0", False)]
    assert [d.name for d in deps.dev] == ["eslint"]


def test_parse_nodejs_package_lock_old_format(tmp_path: Path) -> None:
    """Test parsing legacy package-lock.json 'dependencies' format."""
    (tmp_path / "package.json").write_text(json.dumps({"name": "app"}))
    (tmp_path / "package-lock.json").write_text(
        json.dumps(
            {
                "dependencies": {
                    "react": {"version": "18.0.0"},
                    "eslint": {"version": "8.0.0", "dev": True},
                }
            }
        )
    )
    deps = analyze_deps(tmp_path)
    assert [d.name for d in deps.production] == ["react"]
    assert [d.name for d in deps.dev] == ["eslint"]


def test_parse_nodejs_yarn_lock(tmp_path: Path) -> None:
    """Test parsing yarn.lock."""
    (tmp_path / "package.json").write_text(json.dumps({"name": "app"}))
    (tmp_path / "yarn.lock").write_text(
        'lodash@^4.17.21:\n  version "4.17.21"\n  resolved "https://x"\n'
    )
    deps = analyze_deps(tmp_path)
    assert deps.production[0].name == "lodash"
    assert deps.production[0].version == "4.17.21"


def test_parse_nodejs_pnpm_lock(tmp_path: Path) -> None:
    """Test parsing pnpm-lock.yaml."""
    (tmp_path / "package.json").write_text(json.dumps({"name": "app"}))
    (tmp_path / "pnpm-lock.yaml").write_text("packages:\n  lodash@4.17.21: 4.17.21\n")
    deps = analyze_deps(tmp_path)
    assert deps.production[0].name == "lodash@4.17.21"


def test_parse_nodejs_manifest_fallback(tmp_path: Path) -> None:
    """Test Node.js manifest fallback when no lockfile is present."""
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "^18.0.0"},
                "devDependencies": {"eslint": "^8.0.0"},
            }
        )
    )
    deps = analyze_deps(tmp_path)
    assert [d.name for d in deps.production] == ["react"]
    assert [d.name for d in deps.dev] == ["eslint"]


def test_parse_nodejs_malformed_package_json(tmp_path: Path) -> None:
    """Test Node.js parsing tolerates a malformed package.json."""
    (tmp_path / "package.json").write_text("not json")
    deps = analyze_deps(tmp_path)
    assert deps.ecosystem == "Node.js"
    assert deps.production == []


def test_parse_nodejs_malformed_package_lock(tmp_path: Path) -> None:
    """Test Node.js parsing tolerates a malformed package-lock.json."""
    (tmp_path / "package.json").write_text(json.dumps({"name": "app"}))
    (tmp_path / "package-lock.json").write_text("not json")
    deps = analyze_deps(tmp_path)
    assert deps.production == []


# --- Rust ---


def test_parse_rust_cargo_lock(tmp_path: Path) -> None:
    """Test parsing Cargo.lock."""
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "app"\n')
    (tmp_path / "Cargo.lock").write_text(
        '[[package]]\nname = "serde"\nversion = "1.0.0"\nsource = "registry+x"\n'
    )
    deps = analyze_deps(tmp_path)
    assert deps.ecosystem == "Rust"
    assert deps.production[0].name == "serde"


def test_parse_rust_cargo_toml_fallback(tmp_path: Path) -> None:
    """Test Cargo.toml fallback when no Cargo.lock is present."""
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "app"\n\n'
        "[dependencies]\n"
        'serde = "1.0"\n'
        'tokio = { version = "1.0", features = ["full"] }\n\n'
        "[dev-dependencies]\n"
        'mockall = "0.11"\n'
    )
    deps = analyze_deps(tmp_path)
    assert {d.name for d in deps.production} == {"serde", "tokio"}
    assert [d.name for d in deps.dev] == ["mockall"]


def test_parse_rust_malformed_cargo_toml(tmp_path: Path) -> None:
    """Test Rust parsing tolerates malformed Cargo.toml."""
    (tmp_path / "Cargo.toml").write_text("not [ valid")
    deps = analyze_deps(tmp_path)
    assert deps.production == []


# --- Python ---


def test_parse_python_uv_lock_dev_split(tmp_path: Path) -> None:
    """Test uv.lock parsing splits production and dev dependencies."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\ndependencies = ["fastapi"]\n\n'
        '[dependency-groups]\ndev = ["pytest", "ruff"]\n'
    )
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "0.100.0"\n\n'
        '[[package]]\nname = "pytest"\nversion = "7.4.0"\n\n'
        '[[package]]\nname = "ruff"\nversion = "0.1.0"\n'
    )
    deps = analyze_deps(tmp_path)
    assert [d.name for d in deps.production] == ["fastapi"]
    assert {d.name for d in deps.dev} == {"pytest", "ruff"}
    assert all(d.is_dev for d in deps.dev)
    assert all(not d.is_dev for d in deps.production)


def test_parse_python_uv_lock_graph_split(tmp_path: Path) -> None:
    """Test transitive dev dependencies are classified as dev, not production."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\ndependencies = ["fastapi"]\n\n'
        '[dependency-groups]\ndev = ["pytest"]\n'
    )
    (tmp_path / "uv.lock").write_text(_UV_LOCK_WITH_ROOT)
    deps = analyze_deps(tmp_path)

    # pluggy reaches the tree only through pytest, so it is dev.
    assert {d.name for d in deps.dev} == {"pytest", "pluggy"}
    # shared is reachable from both roots, so production wins.
    assert {d.name for d in deps.production} == {"fastapi", "starlette", "shared"}
    assert all(d.is_dev for d in deps.dev)
    assert all(not d.is_dev for d in deps.production)


def test_parse_python_uv_lock_excludes_root_project(tmp_path: Path) -> None:
    """Test the project itself isn't listed as one of its own dependencies."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "app"\n')
    (tmp_path / "uv.lock").write_text(_UV_LOCK_WITH_ROOT)
    deps = analyze_deps(tmp_path)
    assert "app" not in {d.name for d in [*deps.production, *deps.dev]}


def test_parse_python_pyproject_fallback(tmp_path: Path) -> None:
    """Test pyproject.toml fallback when no uv.lock is present."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "app"\ndependencies = ["fastapi>=0.100"]\n\n'
        '[dependency-groups]\ndev = ["pytest"]\n'
    )
    deps = analyze_deps(tmp_path)
    assert [d.name for d in deps.production] == ["fastapi"]
    assert [d.name for d in deps.dev] == ["pytest"]


def test_parse_python_malformed_uv_lock(tmp_path: Path) -> None:
    """Test Python parsing tolerates a malformed uv.lock via missing pyproject read."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "app"\n')
    (tmp_path / "uv.lock").write_text(
        '[[package]]\nname = "fastapi"\nversion = "0.100.0"\n'
    )
    deps = analyze_deps(tmp_path)
    assert deps.production[0].name == "fastapi"
    assert deps.production[0].is_dev is False


# --- Go ---


def test_parse_go_sum(tmp_path: Path) -> None:
    """Test parsing go.sum."""
    (tmp_path / "go.mod").write_text("module app\n\ngo 1.21\n")
    (tmp_path / "go.sum").write_text(
        "github.com/pkg/errors v0.9.1 h1:abc=\n"
        "github.com/pkg/errors v0.9.1/go.mod h1:def=\n"
    )
    deps = analyze_deps(tmp_path)
    assert deps.ecosystem == "Go"
    assert [d.name for d in deps.production] == ["github.com/pkg/errors"]


def test_parse_go_mod_fallback(tmp_path: Path) -> None:
    """Test go.mod fallback when no go.sum is present."""
    (tmp_path / "go.mod").write_text(
        "module app\n\ngo 1.21\n\nrequire (\n\tgithub.com/foo/bar v1.2.3\n)\n"
    )
    deps = analyze_deps(tmp_path)
    assert [d.name for d in deps.production] == ["github.com/foo/bar"]


def test_parse_go_no_files(tmp_path: Path) -> None:
    """Test Go parsing with neither go.sum nor go.mod content matches."""
    (tmp_path / "go.mod").write_text("")
    deps = analyze_deps(tmp_path)
    assert deps.production == []


# --- Ruby ---


def test_parse_ruby_gemfile_lock(tmp_path: Path) -> None:
    """Test parsing Gemfile.lock."""
    (tmp_path / "Gemfile").write_text('source "https://rubygems.org"\n')
    (tmp_path / "Gemfile.lock").write_text(
        "GEM\n  remote: https://rubygems.org/\n  specs:\n    rails (7.0.4)\n    puma (5.6.5)\n"
    )
    deps = analyze_deps(tmp_path)
    assert deps.ecosystem == "Ruby"
    assert {d.name for d in deps.production} == {"rails", "puma"}


def test_parse_ruby_no_lockfile(tmp_path: Path) -> None:
    """Test Ruby parsing with no Gemfile.lock."""
    (tmp_path / "Gemfile").write_text('source "https://rubygems.org"\n')
    deps = analyze_deps(tmp_path)
    assert deps.production == []


# --- PHP ---


def test_parse_php_composer_lock(tmp_path: Path) -> None:
    """Test parsing composer.lock."""
    (tmp_path / "composer.json").write_text(json.dumps({"name": "app"}))
    (tmp_path / "composer.lock").write_text(
        json.dumps(
            {
                "packages": [{"name": "monolog/monolog", "version": "2.0.0"}],
                "packages-dev": [{"name": "phpunit/phpunit", "version": "9.0.0"}],
            }
        )
    )
    deps = analyze_deps(tmp_path)
    assert deps.ecosystem == "PHP"
    assert [d.name for d in deps.production] == ["monolog/monolog"]
    assert [d.name for d in deps.dev] == ["phpunit/phpunit"]


def test_parse_php_no_lockfile(tmp_path: Path) -> None:
    """Test PHP parsing with no composer.lock."""
    (tmp_path / "composer.json").write_text(json.dumps({"name": "app"}))
    deps = analyze_deps(tmp_path)
    assert deps.production == []


# --- check_outdated ---


def test_check_outdated_unsupported_ecosystem(tmp_path: Path) -> None:
    """Test outdated check for an unsupported ecosystem returns a note."""
    data = DepsResult(production=[], dev=[], ecosystem="Ruby")
    outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is not None and "not supported" in note


def test_check_outdated_npm_success(tmp_path: Path) -> None:
    """Test outdated check for Node.js parses npm's JSON output."""
    data = DepsResult(production=[], dev=[], ecosystem="Node.js")
    fake_result = subprocess.CompletedProcess(
        args=[],
        returncode=1,
        stdout=json.dumps({"react": {"current": "17.0.0", "latest": "18.0.0"}}),
    )
    with patch("meta_one.deps.subprocess.run", return_value=fake_result):
        outdated, note = check_outdated(tmp_path, data)
    assert note is None
    assert outdated[0].name == "react"
    assert outdated[0].latest == "18.0.0"


def test_check_outdated_npm_no_output(tmp_path: Path) -> None:
    """Test outdated check for Node.js when npm reports nothing outdated."""
    data = DepsResult(production=[], dev=[], ecosystem="Node.js")
    fake_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="")
    with patch("meta_one.deps.subprocess.run", return_value=fake_result):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is None


def test_check_outdated_npm_missing(tmp_path: Path) -> None:
    """Test outdated check for Node.js when npm isn't installed."""
    data = DepsResult(production=[], dev=[], ecosystem="Node.js")
    with patch("meta_one.deps.subprocess.run", side_effect=FileNotFoundError):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is not None and "npm not found" in note


def test_check_outdated_npm_timeout(tmp_path: Path) -> None:
    """Test outdated check for Node.js when npm times out."""
    data = DepsResult(production=[], dev=[], ecosystem="Node.js")
    with patch(
        "meta_one.deps.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="npm", timeout=30),
    ):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is not None and "failed" in note


def test_check_outdated_pypi(tmp_path: Path) -> None:
    """Test outdated check for Python queries the PyPI JSON API."""
    data = DepsResult(
        production=[Dependency("requests", "2.0.0", False)], dev=[], ecosystem="Python"
    )

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"info": {"version": "2.31.0"}}).encode()

    with patch("meta_one.deps.urllib.request.urlopen", return_value=FakeResponse()):
        outdated, note = check_outdated(tmp_path, data)
    assert note is None
    assert outdated[0].name == "requests"
    assert outdated[0].latest == "2.31.0"


def test_check_outdated_pypi_satisfied_specifier(tmp_path: Path) -> None:
    """Test a constraint the latest release satisfies isn't reported outdated."""
    data = DepsResult(
        production=[Dependency("typer", ">=0.20.1", False)], dev=[], ecosystem="Python"
    )

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"info": {"version": "0.27.1"}}).encode()

    with patch("meta_one.deps.urllib.request.urlopen", return_value=FakeResponse()):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is None


@pytest.mark.parametrize(
    ("recorded", "latest", "expected"),
    [
        (">=0.20.1", "0.27.1", False),
        (">=0.20.1", "0.19.0", True),
        ("==2.32.3", "2.34.2", True),
        ("~=1.4.2", "1.4.9", False),
        ("~=1.4.2", "1.5.0", True),
        (">=1.0,<2.0", "2.1", True),
        ("2.32.3", "2.34.2", True),
        ("2.34.2", "2.32.3", False),
        ("2.32.3", "2.32.3", False),
        ("weird-version", "2.0", True),
    ],
)
def test_is_outdated(recorded: str, latest: str, expected: bool) -> None:
    """Test constraints are satisfy-checked and plain versions compared by order."""
    assert _is_outdated(recorded, latest) is expected


def test_check_outdated_pypi_network_error(tmp_path: Path) -> None:
    """Test outdated check for Python tolerates network failures per-package."""
    data = DepsResult(
        production=[Dependency("requests", "2.0.0", False)], dev=[], ecosystem="Python"
    )
    with patch(
        "meta_one.deps.urllib.request.urlopen", side_effect=OSError("network down")
    ):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is None


def test_check_outdated_cargo_missing(tmp_path: Path) -> None:
    """Test outdated check for Rust when cargo-outdated isn't installed."""
    data = DepsResult(production=[], dev=[], ecosystem="Rust")
    fake_result = subprocess.CompletedProcess(args=[], returncode=1, stdout="")
    with patch("meta_one.deps.subprocess.run", return_value=fake_result):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is not None and "not installed" in note


def test_check_outdated_cargo_success(tmp_path: Path) -> None:
    """Test outdated check for Rust parses cargo-outdated's JSON output."""
    data = DepsResult(production=[], dev=[], ecosystem="Rust")
    fake_result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps(
            {
                "dependencies": [
                    {"name": "serde", "project": "1.0.0", "latest": "1.5.0"},
                    {"name": "up-to-date", "project": "1.0.0", "latest": "1.0.0"},
                ]
            }
        ),
    )
    with patch("meta_one.deps.subprocess.run", return_value=fake_result):
        outdated, note = check_outdated(tmp_path, data)
    assert note is None
    assert [d.name for d in outdated] == ["serde"]


def test_check_outdated_cargo_not_found(tmp_path: Path) -> None:
    """Test outdated check for Rust when cargo itself isn't installed."""
    data = DepsResult(production=[], dev=[], ecosystem="Rust")
    with patch("meta_one.deps.subprocess.run", side_effect=FileNotFoundError):
        outdated, note = check_outdated(tmp_path, data)
    assert outdated == []
    assert note is not None and "cargo not found" in note
