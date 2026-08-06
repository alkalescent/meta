"""Tests for shared output utilities."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from meta_one.output import (
    Context,
    _supports_color,
    format_table,
    json_out,
    strip_ansi,
    style,
)


def test_strip_ansi_removes_sgr_sequences() -> None:
    """Test complete color sequences are removed."""
    assert strip_ansi("\033[1;31mred\033[0m") == "red"


def test_strip_ansi_tolerates_truncated_escape() -> None:
    """Test an escape with no terminating 'm' doesn't raise."""
    assert strip_ansi("\033[31") == ""
    assert strip_ansi("a\033[31") == "a"


def test_format_table_with_truncated_escape() -> None:
    """Test a cell holding a truncated escape formats instead of raising."""
    rendered = format_table([["\033[31", "value"], ["plain", "other"]])
    assert "value" in rendered
    assert "other" in rendered


def test_format_table_aligns_colored_cells() -> None:
    """Test color codes don't count toward column width."""
    rendered = format_table([["\033[32m✓\033[0m", "ok"], ["✗", "bad"]])
    first, second = (strip_ansi(line) for line in rendered.splitlines())
    assert first.index("ok") == second.index("bad")


def test_style_no_color_context() -> None:
    """Test styling with no_color context."""
    ctx = Context(no_color=True)
    text = "Hello"
    assert style(text, color="red", ctx=ctx) == text


def test_style_supports_color_false() -> None:
    """Test styling returns plain text when the terminal doesn't support color."""
    with patch("meta_one.output._supports_color", return_value=False):
        assert style("Hello", color="red") == "Hello"


def test_style_color_and_bold() -> None:
    """Test styling wraps text in the correct ANSI codes."""
    with patch("meta_one.output._supports_color", return_value=True):
        result = style("Hello", color="red", bold=True)
        assert result == "\033[1;31mHello\033[0m"


def test_style_color_only() -> None:
    """Test styling with only a color, no bold."""
    with patch("meta_one.output._supports_color", return_value=True):
        result = style("Hello", color="green")
        assert result == "\033[32mHello\033[0m"


def test_style_bold_only() -> None:
    """Test styling with only bold, no color."""
    with patch("meta_one.output._supports_color", return_value=True):
        result = style("Hello", bold=True)
        assert result == "\033[1mHello\033[0m"


def test_style_unknown_color() -> None:
    """Test styling with an unrecognized color name is a no-op."""
    with patch("meta_one.output._supports_color", return_value=True):
        assert style("Hello", color="notacolor") == "Hello"


def test_supports_color_no_color_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test NO_COLOR env var disables color support."""
    monkeypatch.setenv("NO_COLOR", "1")
    assert _supports_color() is False


def test_supports_color_dumb_term(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test TERM=dumb disables color support."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "dumb")
    assert _supports_color() is False


def test_supports_color_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test color support is enabled for an interactive TTY."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    with patch("sys.stdout.isatty", return_value=True):
        assert _supports_color() is True


def test_supports_color_not_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test color support is disabled for a non-interactive stream."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    with patch("sys.stdout.isatty", return_value=False):
        assert _supports_color() is False


def test_format_table_empty() -> None:
    """Test formatting empty table."""
    assert format_table([]) == ""


def test_format_table_content() -> None:
    """Test formatting table with content."""
    rows = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
    formatted = format_table(rows)
    assert "Name" in formatted
    assert "Age" in formatted
    assert "Alice" in formatted
    assert "30" in formatted


def test_format_table_strips_ansi_for_alignment() -> None:
    """Test formatting strips embedded ANSI codes when computing column widths."""
    rows = [
        ["\033[31mRed\033[0m", "short"],
        ["longer-name", "value"],
    ]
    formatted = format_table(rows)
    lines = formatted.split("\n")
    assert "Red" in lines[0]
    assert "longer-name" in lines[1]


def test_json_out() -> None:
    """Test JSON serialization."""
    data = {"key": "value", "list": [1, 2, 3]}
    result = json_out(data)
    assert '"key": "value"' in result
    assert "1" in result
    assert "2" in result
    assert "3" in result
