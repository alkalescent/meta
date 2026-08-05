"""Tests for the pep440 module."""

from __future__ import annotations

import pytest

from meta_one.pep440 import is_specifier, parse_version, satisfies


@pytest.mark.parametrize(
    ("text", "release"),
    [
        ("1.2.3", (1, 2, 3)),
        ("v1.2.3", (1, 2, 3)),
        ("0.20.1", (0, 20, 1)),
        ("1!2.0", (2, 0)),
        ("2024.1", (2024, 1)),
    ],
)
def test_parse_version_release(text: str, release: tuple[int, ...]) -> None:
    """Test the release segment is parsed for well-formed versions."""
    parsed = parse_version(text)
    assert parsed is not None
    assert parsed.release == release


def test_parse_version_rejects_garbage() -> None:
    """Test an unparseable version returns None rather than raising."""
    assert parse_version("not-a-version") is None
    assert parse_version("") is None


def test_parse_version_epoch() -> None:
    """Test an epoch outranks a higher release number."""
    low = parse_version("1!1.0")
    high = parse_version("2.0")
    assert low is not None and high is not None
    assert low.key > high.key


@pytest.mark.parametrize(
    ("lower", "higher"),
    [
        ("1.0.0", "1.0.1"),
        ("1.0", "1.0.1"),
        ("1.0rc1", "1.0"),
        ("1.0a1", "1.0b1"),
        ("1.0b1", "1.0rc1"),
        ("1.0.dev1", "1.0a1"),
        ("1.0", "1.0.post1"),
        ("1.9", "1.10"),
    ],
)
def test_version_ordering(lower: str, higher: str) -> None:
    """Test versions sort with dev < pre < final < post."""
    left = parse_version(lower)
    right = parse_version(higher)
    assert left is not None and right is not None
    assert left.key < right.key


def test_trailing_zeros_are_equivalent() -> None:
    """Test 1.0 and 1.0.0 compare equal."""
    short = parse_version("1.0")
    long = parse_version("1.0.0")
    assert short is not None and long is not None
    assert short.key == long.key


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (">=1.0", True),
        ("==1.0", True),
        ("<2", True),
        ("~=1.4", True),
        ("!=1.0", True),
        ("1.0.0", False),
        ("", False),
        ("  ", False),
    ],
)
def test_is_specifier(text: str, expected: bool) -> None:
    """Test constraints are told apart from plain versions."""
    assert is_specifier(text) is expected


@pytest.mark.parametrize(
    ("version", "specifier", "expected"),
    [
        ("0.27.1", ">=0.20.1", True),
        ("0.19.0", ">=0.20.1", False),
        ("2.32.3", "==2.32.3", True),
        ("2.34.2", "==2.32.3", False),
        ("1.5.0", "!=1.5.0", False),
        ("1.5.1", "!=1.5.0", True),
        ("1.4.9", "~=1.4.2", True),
        ("1.5.0", "~=1.4.2", False),
        ("1.4.1", "~=1.4.2", False),
        ("2.0", "~=1.4", False),
        ("1.9", "~=1.4", True),
        ("1.4.7", "==1.4.*", True),
        ("1.5.0", "==1.4.*", False),
        ("1.5.0", "!=1.4.*", True),
        ("1.5", ">=1.0,<2.0", True),
        ("2.1", ">=1.0,<2.0", False),
        ("1.0", "<=1.0", True),
        ("1.0.1", ">1.0", True),
    ],
)
def test_satisfies(version: str, specifier: str, expected: bool) -> None:
    """Test specifier clauses are evaluated against a version."""
    assert satisfies(version, specifier) is expected


def test_satisfies_empty_specifier() -> None:
    """Test an absent constraint accepts anything."""
    assert satisfies("1.0", "") is True
    assert satisfies("1.0", "   ") is True


def test_satisfies_strips_markers_and_extras() -> None:
    """Test environment markers and extras are ignored."""
    assert satisfies("1.5", ">=1.0 ; python_version < '3.9'") is True
    assert satisfies("0.9", ">=1.0 ; python_version < '3.9'") is False
    assert satisfies("1.5", "[socks]>=1.0") is True


def test_satisfies_unparseable_inputs_are_permissive() -> None:
    """Test unparseable versions and bounds don't report a false mismatch."""
    assert satisfies("not-a-version", ">=1.0") is True
    assert satisfies("1.0", ">=not-a-version") is True


def test_satisfies_bare_version_clause() -> None:
    """Test a clause with no operator is treated as an exact match."""
    assert satisfies("1.0", "1.0") is True
    assert satisfies("1.1", "1.0") is False
