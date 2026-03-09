"""Shared output formatting utilities for consistent CLI rendering."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

# Status symbols
SYMBOL_OK = "✓"
SYMBOL_FAIL = "✗"
SYMBOL_WARN = "⚠"
SYMBOL_OPTIONAL = "○"


@dataclass
class Context:
    """Global context carrying CLI flags through all commands."""

    path: str = "."
    json_output: bool = False
    no_color: bool = False
    quiet: bool = False


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def style(
    text: str, color: str = "", bold: bool = False, ctx: Context | None = None
) -> str:
    """Wrap text in ANSI color codes.

    Args:
        text: The text to style.
        color: Color name (red, green, yellow, blue, magenta, cyan, white, gray).
        bold: Whether to bold the text.
        ctx: Context with no_color flag.

    Returns:
        Styled text string, or plain text if color is disabled.
    """
    if ctx and ctx.no_color:
        return text
    if not _supports_color():
        return text

    colors = {
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
        "gray": "90",
    }
    codes: list[str] = []
    if bold:
        codes.append("1")
    if color in colors:
        codes.append(colors[color])
    if not codes:
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


def format_table(rows: list[list[str]], padding: int = 2) -> str:
    """Render rows as an aligned table.

    Args:
        rows: List of rows, each a list of column values.
        padding: Spaces between columns.

    Returns:
        Formatted table string.
    """
    if not rows:
        return ""
    col_widths = [0] * max(len(r) for r in rows)
    for row in rows:
        for i, cell in enumerate(row):
            # Strip ANSI codes for width calculation
            clean = cell
            while "\033[" in clean:
                start = clean.index("\033[")
                end = clean.index("m", start) + 1
                clean = clean[:start] + clean[end:]
            col_widths[i] = max(col_widths[i], len(clean))

    lines: list[str] = []
    for row in rows:
        parts: list[str] = []
        for i, cell in enumerate(row):
            clean = cell
            while "\033[" in clean:
                start = clean.index("\033[")
                end = clean.index("m", start) + 1
                clean = clean[:start] + clean[end:]
            pad = col_widths[i] - len(clean) + padding if i < len(row) - 1 else 0
            parts.append(cell + " " * pad)
        lines.append("".join(parts).rstrip())
    return "\n".join(lines)


def json_out(data: Any) -> str:
    """Serialize data to indented JSON.

    Args:
        data: Data to serialize.

    Returns:
        JSON string.
    """
    return json.dumps(data, indent=2, default=str)
