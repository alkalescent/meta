"""Project type detection from marker files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


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
    try:
        content = pyproject_path.read_text()
        for dep_name, framework in PYTHON_FRAMEWORKS.items():
            if dep_name in content.lower():
                return framework
    except OSError:
        pass
    return ""


def _detect_csproj(root: Path) -> ProjectInfo | None:
    """Detect .NET project from .csproj or .sln files.

    Args:
        root: Project root directory.

    Returns:
        ProjectInfo if .NET project detected, else None.
    """
    csproj_files = list(root.glob("*.csproj")) + list(root.glob("**/*.csproj"))
    sln_files = list(root.glob("*.sln"))
    if csproj_files or sln_files:
        marker = str(csproj_files[0].name) if csproj_files else str(sln_files[0].name)
        return ProjectInfo(
            project_type=".NET",
            language="C#",
            marker_file=marker,
        )
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


def detect_all_project_types(root: Path) -> list[ProjectInfo]:
    """Detect all project types present in the directory.

    Args:
        root: Directory to scan.

    Returns:
        List of all detected ProjectInfo objects.
    """
    results: list[ProjectInfo] = []
    for marker_file, (project_type, language) in MARKER_MAP.items():
        if (root / marker_file).exists():
            framework = ""
            if project_type == "Node.js":
                framework = _detect_node_framework(root)
                language = _detect_node_language(root)
            elif project_type == "Python":
                framework = _detect_python_framework(root)
            results.append(
                ProjectInfo(
                    project_type=project_type,
                    framework=framework,
                    language=language,
                    marker_file=marker_file,
                )
            )
    dotnet = _detect_csproj(root)
    if dotnet:
        results.append(dotnet)
    return results
