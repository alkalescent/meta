"""Dependency parsing for the meta CLI tool.

This module parses dependency manifests and lockfiles across ecosystems.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Dependency:
    """Represents a single parsed dependency."""

    name: str
    version: str
    is_dev: bool


@dataclass
class DepsResult:
    """Results of a dependency parsing operation."""

    production: list[Dependency]
    dev: list[Dependency]
    ecosystem: str


def _normalize_pkg_name(name: str) -> str:
    """Normalize a package name for case/separator-insensitive comparison (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _dev_dependency_names(pyproject: Path) -> set[str]:
    """Extract normalized package names listed under [dependency-groups].dev.

    Args:
        pyproject: Path to pyproject.toml.

    Returns:
        Set of normalized package names.
    """
    if not pyproject.exists():
        return set()
    try:
        toml_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:
        return set()
    names: set[str] = set()
    for dep in toml_data.get("dependency-groups", {}).get("dev", []):
        match = re.match(r"^([a-zA-Z0-9_.\-]+)", dep)
        if match:
            names.add(_normalize_pkg_name(match.group(1)))
    return names


def analyze_deps(root: Path) -> DepsResult:
    """Analyze dependencies in the given root directory.

    Args:
        root: The root directory to scan.

    Returns:
        A DepsResult containing parsed production and dev dependencies.
    """
    if (root / "package.json").exists():
        return _parse_nodejs(root)
    if (root / "Cargo.toml").exists():
        return _parse_rust(root)
    if (root / "pyproject.toml").exists():
        return _parse_python(root)
    if (root / "go.mod").exists():
        return _parse_go(root)
    if (root / "Gemfile").exists():
        return _parse_ruby(root)
    if (root / "composer.json").exists():
        return _parse_php(root)

    return DepsResult([], [], "unknown")


def _parse_nodejs(root: Path) -> DepsResult:
    """Parse Node.js dependencies."""
    production: list[Dependency] = []
    dev: list[Dependency] = []

    package_json = root / "package.json"
    package_lock = root / "package-lock.json"
    yarn_lock = root / "yarn.lock"
    pnpm_lock = root / "pnpm-lock.yaml"

    try:
        with package_json.open(encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception:
        manifest = {}

    if package_lock.exists():
        try:
            with package_lock.open(encoding="utf-8") as f:
                lock = json.load(f)
                if "packages" in lock:
                    deps = lock["packages"].get("", {}).get("dependencies", {})
                    dev_deps = lock["packages"].get("", {}).get("devDependencies", {})
                    for name, version in deps.items():
                        production.append(Dependency(name, version, False))
                    for name, version in dev_deps.items():
                        dev.append(Dependency(name, version, True))
                elif "dependencies" in lock:
                    for name, meta in lock["dependencies"].items():
                        is_dev = meta.get("dev", False)
                        dep = Dependency(name, meta.get("version", ""), is_dev)
                        if is_dev:
                            dev.append(dep)
                        else:
                            production.append(dep)
        except Exception:
            pass
    elif yarn_lock.exists():
        try:
            content = yarn_lock.read_text(encoding="utf-8")
            matches = re.finditer(
                r'^"?([^@\n]+)@[^:\n]+:\n\s+version\s+"([^"]+)"', content, re.MULTILINE
            )
            for match in matches:
                production.append(Dependency(match.group(1), match.group(2), False))
        except Exception:
            pass
    elif pnpm_lock.exists():
        try:
            content = pnpm_lock.read_text(encoding="utf-8")
            matches = re.finditer(r"^  /?([^:]+): ([^\s]+)", content, re.MULTILINE)
            for match in matches:
                production.append(Dependency(match.group(1), match.group(2), False))
        except Exception:
            pass
    else:
        for name, version in manifest.get("dependencies", {}).items():
            production.append(Dependency(name, str(version), False))
        for name, version in manifest.get("devDependencies", {}).items():
            dev.append(Dependency(name, str(version), True))

    return DepsResult(production, dev, "Node.js")


def _parse_rust(root: Path) -> DepsResult:
    """Parse Rust dependencies."""
    production: list[Dependency] = []
    dev: list[Dependency] = []
    cargo_lock = root / "Cargo.lock"
    cargo_toml = root / "Cargo.toml"

    if cargo_lock.exists():
        try:
            content = cargo_lock.read_text(encoding="utf-8")
            matches = re.finditer(
                r'\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"', content
            )
            for match in matches:
                production.append(Dependency(match.group(1), match.group(2), False))
        except Exception:
            pass
    elif cargo_toml.exists():
        try:
            content = cargo_toml.read_text(encoding="utf-8")
            toml_data = tomllib.loads(content)
            for name, meta in toml_data.get("dependencies", {}).items():
                version = meta if isinstance(meta, str) else meta.get("version", "")
                production.append(Dependency(name, version, False))
            for name, meta in toml_data.get("dev-dependencies", {}).items():
                version = meta if isinstance(meta, str) else meta.get("version", "")
                dev.append(Dependency(name, version, True))
        except Exception:
            pass

    return DepsResult(production, dev, "Rust")


def _parse_python(root: Path) -> DepsResult:
    """Parse Python dependencies."""
    production: list[Dependency] = []
    dev: list[Dependency] = []

    uv_lock = root / "uv.lock"
    pyproject = root / "pyproject.toml"

    if uv_lock.exists():
        try:
            content = uv_lock.read_text(encoding="utf-8")
            matches = re.finditer(
                r'\[\[package\]\]\nname = "([^"]+)"\nversion = "([^"]+)"', content
            )
            dev_names = _dev_dependency_names(pyproject)
            for match in matches:
                name, version = match.group(1), match.group(2)
                is_dev = _normalize_pkg_name(name) in dev_names
                dep = Dependency(name, version, is_dev)
                (dev if is_dev else production).append(dep)
        except Exception:
            pass
    elif pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            toml_data = tomllib.loads(content)
            deps = toml_data.get("project", {}).get("dependencies", [])
            for dep in deps:
                match = re.match(r"^([a-zA-Z0-9_\-]+)(.*)$", dep)
                if match:
                    production.append(
                        Dependency(match.group(1), match.group(2).strip(), False)
                    )
            dev_deps = toml_data.get("dependency-groups", {}).get("dev", [])
            for dep in dev_deps:
                match = re.match(r"^([a-zA-Z0-9_\-]+)(.*)$", dep)
                if match:
                    dev.append(Dependency(match.group(1), match.group(2).strip(), True))
        except Exception:
            pass

    return DepsResult(production, dev, "Python")


def _parse_go(root: Path) -> DepsResult:
    """Parse Go dependencies."""
    production: list[Dependency] = []
    go_sum = root / "go.sum"
    go_mod = root / "go.mod"

    if go_sum.exists():
        try:
            lines = go_sum.read_text(encoding="utf-8").splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and not parts[1].endswith("/go.mod"):
                    production.append(Dependency(parts[0], parts[1], False))
        except Exception:
            pass
    elif go_mod.exists():
        try:
            content = go_mod.read_text(encoding="utf-8")
            matches = re.finditer(r"^\s*([^\s]+)\s+(v[^\s]+)", content, re.MULTILINE)
            for match in matches:
                if match.group(1) != "require":
                    production.append(Dependency(match.group(1), match.group(2), False))
        except Exception:
            pass

    return DepsResult(production, [], "Go")


def _parse_ruby(root: Path) -> DepsResult:
    """Parse Ruby dependencies."""
    production: list[Dependency] = []
    gemfile_lock = root / "Gemfile.lock"

    if gemfile_lock.exists():
        try:
            content = gemfile_lock.read_text(encoding="utf-8")
            matches = re.finditer(r"^    ([^ ]+) \(([^)]+)\)", content, re.MULTILINE)
            for match in matches:
                production.append(Dependency(match.group(1), match.group(2), False))
        except Exception:
            pass

    return DepsResult(production, [], "Ruby")


def _parse_php(root: Path) -> DepsResult:
    """Parse PHP dependencies."""
    production: list[Dependency] = []
    dev: list[Dependency] = []
    composer_lock = root / "composer.lock"

    if composer_lock.exists():
        try:
            with composer_lock.open(encoding="utf-8") as f:
                lock = json.load(f)
                for pkg in lock.get("packages", []):
                    production.append(
                        Dependency(pkg.get("name", ""), pkg.get("version", ""), False)
                    )
                for pkg in lock.get("packages-dev", []):
                    dev.append(
                        Dependency(pkg.get("name", ""), pkg.get("version", ""), True)
                    )
        except Exception:
            pass

    return DepsResult(production, dev, "PHP")


@dataclass
class OutdatedDependency:
    """A dependency that has a newer version available."""

    name: str
    current: str
    latest: str


def check_outdated(
    root: Path, data: DepsResult
) -> tuple[list[OutdatedDependency], str | None]:
    """Check for outdated dependencies for the given ecosystem.

    Args:
        root: The root directory of the project.
        data: Already-parsed dependency data (used for ecosystem + names).

    Returns:
        A tuple of (outdated dependencies found, an optional note explaining
        a skipped/unsupported check).
    """
    if data.ecosystem == "Node.js":
        return _check_outdated_npm(root)
    if data.ecosystem == "Python":
        return _check_outdated_pypi(data)
    if data.ecosystem == "Rust":
        return _check_outdated_cargo(root)
    return [], f"Outdated check not supported for {data.ecosystem} projects."


def _check_outdated_npm(root: Path) -> tuple[list[OutdatedDependency], str | None]:
    """Check outdated Node.js dependencies via `npm outdated --json`."""
    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        # npm exits 1 when outdated deps are found; stdout is still valid JSON.
        if not result.stdout.strip():
            return [], None
        payload = json.loads(result.stdout)
        outdated = [
            OutdatedDependency(name, info.get("current", "?"), info.get("latest", "?"))
            for name, info in payload.items()
        ]
        return outdated, None
    except FileNotFoundError:
        return [], "Outdated check skipped: npm not found."
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return [], "Outdated check failed: could not query npm."


def _check_outdated_pypi(
    data: DepsResult,
) -> tuple[list[OutdatedDependency], str | None]:
    """Check outdated Python dependencies via the PyPI JSON API."""
    outdated: list[OutdatedDependency] = []
    for dep in [*data.production, *data.dev]:
        try:
            with urllib.request.urlopen(
                f"https://pypi.org/pypi/{dep.name}/json", timeout=5
            ) as resp:
                info = json.loads(resp.read())
            latest = info.get("info", {}).get("version", "")
            if latest and latest != dep.version:
                outdated.append(OutdatedDependency(dep.name, dep.version, latest))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            continue
    return outdated, None


def _check_outdated_cargo(root: Path) -> tuple[list[OutdatedDependency], str | None]:
    """Check outdated Rust dependencies via the `cargo-outdated` plugin."""
    try:
        result = subprocess.run(
            ["cargo", "outdated", "--format", "json"],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return [], "Outdated check skipped: cargo-outdated not installed."
        payload = json.loads(result.stdout)
        outdated = [
            OutdatedDependency(
                entry.get("name", ""),
                entry.get("project", "?"),
                entry.get("latest", "?"),
            )
            for entry in payload.get("dependencies", [])
            if entry.get("latest") not in (None, entry.get("project"))
        ]
        return outdated, None
    except FileNotFoundError:
        return [], "Outdated check skipped: cargo not found."
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return [], "Outdated check failed: could not query cargo."
