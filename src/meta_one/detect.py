"""Project type detection from marker files."""

from __future__ import annotations

import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from meta_one.walk import SKIP_DIRS


@dataclass
class ProjectInfo:
    """Detected project information."""

    project_type: str
    framework: str = ""
    language: str = ""
    marker_file: str = ""


# Marker file -> (project_type, language)
MARKER_MAP: dict[str, tuple[str, str]] = {
    "package.json": ("Node.js", "JavaScript"),
    "Cargo.toml": ("Rust", "Rust"),
    "pyproject.toml": ("Python", "Python"),
    "setup.py": ("Python", "Python"),
    "go.mod": ("Go", "Go"),
    "pom.xml": ("Java", "Java"),
    "build.gradle": ("Java", "Java"),
    "build.gradle.kts": ("Kotlin", "Kotlin"),
    "Gemfile": ("Ruby", "Ruby"),
    "composer.json": ("PHP", "PHP"),
}

# Node.js framework detection: dependency name -> framework
NODE_FRAMEWORKS: dict[str, str] = {
    "next": "Next.js",
    "nuxt": "Nuxt",
    "@angular/core": "Angular",
    "vue": "Vue",
    "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit",
    "express": "Express",
    "fastify": "Fastify",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "astro": "Astro",
}

# Python framework detection: dependency name -> framework
PYTHON_FRAMEWORKS: dict[str, str] = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "typer": "Typer CLI",
    "click": "Click CLI",
    "scrapy": "Scrapy",
}


def _detect_node_framework(root: Path) -> str:
    """Detect Node.js framework from package.json dependencies.

    Args:
        root: Project root directory.

    Returns:
        Framework name, or empty string if not detected.
    """
    pkg_path = root / "package.json"
    if not pkg_path.exists():
        return ""
    try:
        with open(pkg_path) as f:
            pkg = json.load(f)
        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))
        for dep_name, framework in NODE_FRAMEWORKS.items():
            if dep_name in all_deps:
                return framework
    except (json.JSONDecodeError, OSError):
        pass
    return ""


def _detect_node_language(root: Path) -> str:
    """Detect if a Node.js project uses TypeScript.

    Args:
        root: Project root directory.

    Returns:
        'TypeScript' if tsconfig.json exists, else 'JavaScript'.
    """
    if (root / "tsconfig.json").exists():
        return "TypeScript"
    return "JavaScript"


def _declared_python_deps(pyproject_path: Path) -> set[str]:
    """Collect declared dependency names from a pyproject.toml.

    Covers [project].dependencies, [project.optional-dependencies], and
    [dependency-groups]. Names only, so a framework mentioned in a comment or
    description isn't mistaken for a dependency.

    Args:
        pyproject_path: Path to pyproject.toml.

    Returns:
        Set of lowercased dependency names.
    """
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return set()

    specs: list[str] = list(data.get("project", {}).get("dependencies", []))
    for group in data.get("project", {}).get("optional-dependencies", {}).values():
        specs.extend(group)
    for group in data.get("dependency-groups", {}).values():
        specs.extend(s for s in group if isinstance(s, str))

    names: set[str] = set()
    for spec in specs:
        match = re.match(r"^\s*([A-Za-z0-9._-]+)", spec)
        if match:
            names.add(match.group(1).lower())
    return names


def _detect_python_framework(root: Path) -> str:
    """Detect Python framework from pyproject.toml dependencies.

    Args:
        root: Project root directory.

    Returns:
        Framework name, or empty string if not detected.
    """
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return ""
    declared = _declared_python_deps(pyproject_path)
    for dep_name, framework in PYTHON_FRAMEWORKS.items():
        if dep_name in declared:
            return framework
    return ""


def _detect_csproj(root: Path) -> ProjectInfo | None:
    """Detect .NET project from .csproj or .sln files.

    Args:
        root: Project root directory.

    Returns:
        ProjectInfo if .NET project detected, else None.
    """
    marker = ""
    for _dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for filename in filenames:
            if filename.endswith(".csproj"):
                return ProjectInfo(
                    project_type=".NET", language="C#", marker_file=filename
                )
            if not marker and filename.endswith(".sln"):
                marker = filename
    if marker:
        return ProjectInfo(project_type=".NET", language="C#", marker_file=marker)
    return None


def detect_project_type(root: Path) -> ProjectInfo:
    """Detect the project type from marker files in the given directory.

    Args:
        root: Directory to scan for project marker files.

    Returns:
        ProjectInfo with detected type, framework, and language.
    """
    for marker_file, (project_type, language) in MARKER_MAP.items():
        if (root / marker_file).exists():
            framework = ""
            if project_type == "Node.js":
                framework = _detect_node_framework(root)
                language = _detect_node_language(root)
            elif project_type == "Python":
                framework = _detect_python_framework(root)
            return ProjectInfo(
                project_type=project_type,
                framework=framework,
                language=language,
                marker_file=marker_file,
            )

    # Check for .NET projects
    dotnet = _detect_csproj(root)
    if dotnet:
        return dotnet

    return ProjectInfo(project_type="Unknown")
