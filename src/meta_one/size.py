"""Codebase size analysis."""

from __future__ import annotations

import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LanguageStats:
    """Statistics for a programming language."""

    name: str
    files: int
    lines: int
    percentage: float


@dataclass
class DirStats:
    """Statistics for a directory."""

    path: str
    files: int
    lines: int


@dataclass
class FileStats:
    """Statistics for a file."""

    path: str
    lines: int


@dataclass
class SizeResult:
    """Result of a size analysis."""

    languages: list[LanguageStats]
    directories: list[DirStats]
    largest_files: list[FileStats]
    total_files: int
    total_lines: int


EXTENSION_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".r": "R",
    ".R": "R",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".hs": "Haskell",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".less": "Less",
    ".html": "HTML",
    ".htm": "HTML",
    ".xml": "XML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".txt": "Text",
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".proto": "Protocol Buffers",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".zig": "Zig",
    ".nim": "Nim",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".tf": "Terraform",
    ".dockerfile": "Dockerfile",
}


def _is_comment(line: str) -> bool:
    """Check if a line is a comment."""
    line = line.lstrip()
    return any(
        line.startswith(prefix)
        for prefix in (
            "#",
            "//",
            "/*",
            "*",
            "<!--",
            "--",
        )
    )


def _count_lines(path: Path, code_only: bool) -> int:
    """Count lines in a file."""
    try:
        lines = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                if code_only:
                    if not line.strip():
                        continue
                    if _is_comment(line):
                        continue
                lines += 1
        return lines
    except (UnicodeDecodeError, OSError):
        return 0


def _get_files_git(root: Path) -> list[str]:
    """Get tracked files using git ls-files."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.splitlines() if f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def _get_files_manual(root: Path) -> list[str]:
    """Walk directory manually, skipping common ignore dirs."""
    skip_dirs = {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".venv",
        "__pycache__",
        "venv",
        "env",
    }
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in skip_dirs and not d.startswith(".")
        ]
        rel_dir = Path(dirpath).relative_to(root)
        for f in filenames:
            if str(rel_dir) == ".":
                files.append(f)
            else:
                files.append(str(rel_dir / f))
    return files


def _get_language(path: Path) -> str | None:
    """Get language for a file path."""
    if path.name.lower() == "dockerfile":
        return "Dockerfile"
    ext = path.suffix.lower()
    return EXTENSION_MAP.get(ext)


def analyze_size(
    root: Path, sort_by: str = "lines", depth: int = 3, code_only: bool = False
) -> SizeResult:
    """Analyze the codebase size.

    Args:
        root: The root directory to analyze.
        sort_by: How to sort the results ("lines", "files").
        depth: The maximum directory depth to show in stats.
        code_only: Whether to skip empty lines and comments.

    Returns:
        A SizeResult object containing the analysis.
    """
    if (root / ".git").exists():
        files = _get_files_git(root)
        if not files:
            files = _get_files_manual(root)
    else:
        files = _get_files_manual(root)

    total_files = 0
    total_lines = 0

    lang_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "lines": 0}
    )
    dir_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "lines": 0}
    )
    file_stats: list[FileStats] = []

    for f_str in files:
        f_path = Path(f_str)
        abs_path = root / f_path
        if not abs_path.is_file():
            continue

        lang = _get_language(f_path)
        if not lang:
            continue

        lines = _count_lines(abs_path, code_only)
        if lines == 0:
            continue

        total_files += 1
        total_lines += lines

        lang_counts[lang]["files"] += 1
        lang_counts[lang]["lines"] += lines

        file_stats.append(FileStats(path=f_str, lines=lines))

        # Directory stats
        parts = f_path.parts[:-1]
        for i in range(1, min(len(parts) + 1, depth + 1)):
            dir_path = "/".join(parts[:i])
            if not dir_path:
                continue
            dir_counts[dir_path]["files"] += 1
            dir_counts[dir_path]["lines"] += lines

    languages = []
    for name, stats in lang_counts.items():
        pct = (stats["lines"] / total_lines * 100) if total_lines else 0.0
        languages.append(
            LanguageStats(
                name=name,
                files=stats["files"],
                lines=stats["lines"],
                percentage=pct,
            )
        )

    directories = [
        DirStats(path=p, files=s["files"], lines=s["lines"])
        for p, s in dir_counts.items()
    ]

    # Sort
    if sort_by == "lines":
        languages.sort(key=lambda x: x.lines, reverse=True)
        directories.sort(key=lambda x: x.lines, reverse=True)
    else:
        languages.sort(key=lambda x: x.files, reverse=True)
        directories.sort(key=lambda x: x.files, reverse=True)

    file_stats.sort(key=lambda x: x.lines, reverse=True)
    largest_files = file_stats[:10]

    return SizeResult(
        languages=languages,
        directories=directories,
        largest_files=largest_files,
        total_files=total_files,
        total_lines=total_lines,
    )
