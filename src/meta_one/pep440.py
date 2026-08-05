"""Minimal PEP 440 version parsing and specifier matching.

Implements the subset needed to answer "does this released version satisfy the
constraint a project declared?". Deliberately dependency-free: `packaging` is a
dev-only dependency, and the runtime is meant to need nothing but typer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_VERSION_RE = re.compile(
    r"""
    ^\s*v?
    (?:(?P<epoch>\d+)!)?
    (?P<release>\d+(?:\.\d+)*)
    (?:[-_.]?(?P<pre_l>a|b|c|rc|alpha|beta|pre|preview)[-_.]?(?P<pre_n>\d+)?)?
    (?:[-_.]?(?:post|rev|r)[-_.]?(?P<post_n>\d+)?)?
    (?:[-_.]?dev[-_.]?(?P<dev_n>\d+)?)?
    (?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Pre-release letters that sort equivalently.
_PRE_RANK: dict[str, int] = {
    "a": 0,
    "alpha": 0,
    "b": 1,
    "beta": 1,
    "c": 2,
    "rc": 2,
    "pre": 2,
    "preview": 2,
}

_OPERATORS = ("===", "==", "!=", "<=", ">=", "~=", "<", ">")

# A dependency string records a constraint rather than a version whenever it
# opens with one of these characters.
_SPECIFIER_START = set("<>=!~^*")


@dataclass(frozen=True)
class Version:
    """A parsed PEP 440 version, reduced to what ordering needs."""

    epoch: int
    release: tuple[int, ...]
    pre: tuple[int, int] | None
    post: int | None
    dev: int | None

    @property
    def key(self) -> tuple:
        """Sort key placing dev < pre < final < post.

        Returns:
            tuple: Comparable key for this version.
        """
        release = self.release
        while len(release) > 1 and release[-1] == 0:
            release = release[:-1]

        if self.pre is not None:
            stage = (0, *self.pre)
        elif self.dev is not None and self.post is None:
            stage = (-1, 0, 0)
        elif self.post is not None:
            stage = (2, self.post, 0)
        else:
            stage = (1, 0, 0)

        return (self.epoch, release, stage, self.dev if self.dev is not None else -1)


def parse_version(text: str) -> Version | None:
    """Parse a version string.

    Args:
        text: Version string, e.g. "1.4.2rc1".

    Returns:
        Version | None: Parsed version, or None if it isn't PEP 440 shaped.
    """
    match = _VERSION_RE.match(text)
    if not match:
        return None

    pre: tuple[int, int] | None = None
    if match.group("pre_l"):
        rank = _PRE_RANK[match.group("pre_l").lower()]
        pre = (rank, int(match.group("pre_n") or 0))

    post = None
    if "post" in text.lower() or "rev" in text.lower() or match.group("post_n"):
        if match.group("post_n") is not None:
            post = int(match.group("post_n"))

    dev = None
    if match.group("dev_n") is not None:
        dev = int(match.group("dev_n"))
    elif re.search(r"[-_.]?dev(?![a-z])", text, re.IGNORECASE):
        dev = 0

    return Version(
        epoch=int(match.group("epoch") or 0),
        release=tuple(int(p) for p in match.group("release").split(".")),
        pre=pre,
        post=post,
        dev=dev,
    )


def is_specifier(text: str) -> bool:
    """Report whether a string is a constraint rather than a plain version.

    Args:
        text: Recorded dependency version string.

    Returns:
        bool: True if the string opens with a comparison operator.
    """
    stripped = text.strip()
    return bool(stripped) and stripped[0] in _SPECIFIER_START


def _compare(left: Version, right: Version, operator: str) -> bool:
    """Apply an ordering operator to two parsed versions.

    Args:
        left: Left-hand version.
        right: Right-hand version.
        operator: One of <, <=, >, >=.

    Returns:
        bool: Result of the comparison.
    """
    if operator == "<":
        return left.key < right.key
    if operator == "<=":
        return left.key <= right.key
    if operator == ">":
        return left.key > right.key
    return left.key >= right.key


def _matches_wildcard(version: Version, pattern: str) -> bool:
    """Match a version against a release prefix such as "1.4.*".

    Args:
        version: Version under test.
        pattern: Constraint version ending in ".*".

    Returns:
        bool: True if the version's release starts with the given prefix.
    """
    prefix = parse_version(pattern[:-2])
    if prefix is None:
        return False
    head = version.release[: len(prefix.release)]
    return head == prefix.release


def _satisfies_clause(version: Version, operator: str, bound: str) -> bool:
    """Evaluate one specifier clause against a version.

    Args:
        version: Version under test.
        operator: Comparison operator.
        bound: Right-hand version string, possibly a ".*" wildcard.

    Returns:
        bool: True if the clause holds, or if the bound can't be parsed.
    """
    if bound.endswith(".*"):
        matched = _matches_wildcard(version, bound)
        if operator == "==":
            return matched
        if operator == "!=":
            return not matched
        bound = bound[:-2]

    target = parse_version(bound)
    if target is None:
        return True

    if operator in ("==", "==="):
        return version.key == target.key
    if operator == "!=":
        return version.key != target.key
    if operator == "~=":
        # ~=X.Y means >=X.Y and ==X.*; ~=X.Y.Z means >=X.Y.Z and ==X.Y.*.
        if len(target.release) < 2:
            return version.key >= target.key
        ceiling = Version(
            epoch=target.epoch,
            release=(*target.release[:-2], target.release[-2] + 1),
            pre=None,
            post=None,
            dev=None,
        )
        return version.key >= target.key and version.key < ceiling.key
    return _compare(version, target, operator)


def satisfies(version: str, specifier: str) -> bool:
    """Check whether a version satisfies a comma-separated specifier set.

    Environment markers and extras are ignored; an empty or unparseable
    specifier is treated as unconstrained.

    Args:
        version: Released version, e.g. "0.27.1".
        specifier: Constraint, e.g. ">=0.20.1,<1.0".

    Returns:
        bool: True if every clause holds.
    """
    parsed = parse_version(version)
    if parsed is None:
        return True

    # Drop environment markers and extras: "foo[bar]>=1 ; python_version<'3.9'".
    constraint = specifier.split(";")[0]
    constraint = re.sub(r"\[[^\]]*\]", "", constraint).strip()
    if not constraint:
        return True

    for raw in constraint.split(","):
        clause = raw.strip()
        if not clause:
            continue
        for operator in _OPERATORS:
            if clause.startswith(operator):
                bound = clause[len(operator) :].strip()
                if bound and not _satisfies_clause(parsed, operator, bound):
                    return False
                break
        else:
            # No recognised operator: treat as an exact version.
            target = parse_version(clause)
            if target is not None and parsed.key != target.key:
                return False
    return True
