"""Shared filesystem traversal settings."""

from __future__ import annotations

# Directories that never hold first-party source and are expensive to descend.
# Callers additionally skip dot-directories.
SKIP_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".venv",
        "__pycache__",
        "venv",
        "env",
    }
)
