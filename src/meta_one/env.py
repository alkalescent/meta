"""Environment variable analysis."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from meta_one.walk import SKIP_DIRS


@dataclass
class EnvVar:
    """Environment variable information."""

    name: str
    status: str
    is_required: bool
    used_in: list[str]


@dataclass
class EnvResult:
    """Result of environment variable analysis."""

    expected_vars: list[EnvVar]
    total_expected: int


def _parse_env_file(path: Path) -> dict[str, str | None]:
    """Parse a .env file and return a dictionary of keys and default values.

    Values are strings if a default exists, or None if no default.

    Args:
        path: Path to the .env file.

    Returns:
        Dictionary of variables.
    """
    vars_dict: dict[str, str | None] = {}
    if not path.exists():
        return vars_dict

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (
                        val.startswith("'") and val.endswith("'")
                    ):
                        val = val[1:-1]
                    vars_dict[key] = val if val else None
                else:
                    vars_dict[line.strip()] = None
    except OSError:
        pass
    return vars_dict


def _find_env_usages(root: Path, keys: set[str]) -> dict[str, list[str]]:
    """Scan source files for usages of environment variables.

    Args:
        root: The root directory to scan.
        keys: Set of expected variable names.

    Returns:
        Dictionary mapping variable names to lists of file paths.
    """
    usages: dict[str, list[str]] = {k: [] for k in keys}
    if not keys:
        return usages

    # Patterns for different languages
    # Group 1 matches the key
    patterns = [
        re.compile(r"process\.env\.([A-Z0-9_]+)"),
        re.compile(r"os\.environ(?:\[|\.get\()[\"']([A-Z0-9_]+)[\"']"),
        re.compile(r"os\.getenv\([\"']([A-Z0-9_]+)[\"']\)", re.IGNORECASE),
        re.compile(r"std::env::var\([\"']([A-Z0-9_]+)[\"']\)"),
        re.compile(r"ENV\[[\"']([A-Z0-9_]+)[\"']\]"),
        re.compile(r"getenv\([\"']([A-Z0-9_]+)[\"']\)", re.IGNORECASE),
    ]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for filename in filenames:
            # Skip likely binary or non-source files
            if filename.endswith((".pyc", ".png", ".jpg", ".pdf")):
                continue
            fpath = Path(dirpath) / filename
            rel_path = fpath.relative_to(root)
            try:
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                    for pattern in patterns:
                        for match in pattern.finditer(content):
                            key = match.group(1)
                            if key in keys and str(rel_path) not in usages[key]:
                                usages[key].append(str(rel_path))
            except (UnicodeDecodeError, OSError):
                continue

    return usages


def analyze_env(root: Path) -> EnvResult:
    """Analyze environment variables in the project.

    Args:
        root: The root directory of the project.

    Returns:
        EnvResult containing expected variables and their status.
    """
    example_files = [".env.example", ".env.sample", ".env.template"]
    expected_vars: dict[str, str | None] = {}

    for example in example_files:
        path = root / example
        if path.exists():
            expected_vars.update(_parse_env_file(path))

    actual_vars = _parse_env_file(root / ".env")

    usages = _find_env_usages(root, set(expected_vars.keys()))

    results: list[EnvVar] = []
    for name, default_val in expected_vars.items():
        is_required = default_val is None

        # Check if set in .env or environment
        if name in actual_vars and actual_vars[name]:
            status = "set"
        elif name in os.environ and os.environ[name]:
            status = "set"
        elif not is_required:
            status = "optional"
        else:
            status = "missing"

        results.append(
            EnvVar(
                name=name,
                status=status,
                is_required=is_required,
                used_in=usages.get(name, []),
            )
        )

    # Sort so missing/required are first, then set, then optional
    def sort_key(var: EnvVar) -> int:
        if var.status == "missing":
            return 0
        if var.status == "set":
            return 1
        return 2

    results.sort(key=sort_key)

    return EnvResult(
        expected_vars=results,
        total_expected=len(results),
    )
