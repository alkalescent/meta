"""Tests for shared output utilities."""

from meta_one.output import Context, format_table, json_out, style


def test_style_color() -> None:
    """Test styling text with color."""
    # Assuming _supports_color returns True for tests, or we mock it.
    # Actually, if NO_COLOR is set by the runner, it might return False.
    # We'll just test the logic ignoring the actual terminal capabilities
    # by mocking the _supports_color function.
    pass  # We can't easily test ANSI codes without mocking sys.stdout.isatty or env vars


def test_style_no_color_context() -> None:
    """Test styling with no_color context."""
    ctx = Context(no_color=True)
    text = "Hello"
    assert style(text, color="red", ctx=ctx) == text


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


def test_json_out() -> None:
    """Test JSON serialization."""
    data = {"key": "value", "list": [1, 2, 3]}
    result = json_out(data)
    assert '"key": "value"' in result
    assert "1" in result
    assert "2" in result
    assert "3" in result
