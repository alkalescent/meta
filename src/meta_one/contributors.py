"""Git contributor analysis for the meta CLI tool.

Analyzes Git repository contributor statistics and file churn.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Contributor:
    """Represents a Git contributor."""

    name: str
    commits: int
    insertions: int
    deletions: int
    last_active: str


@dataclass
class RecentFile:
    """Represents a recently modified file."""

    path: str
    commits: int
    authors: int


@dataclass
class ChurnFile:
    """Represents a file with high churn."""

    path: str
    commits: int


@dataclass
class ContributorsResult:
    """Results of a contributor analysis operation."""

    contributors: list[Contributor]
    recent_files: list[RecentFile]
    churn_hotspots: list[ChurnFile]


def _run_git(command: list[str], root: Path) -> str:
    """Run a Git command and return its output."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root)] + command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def analyze_contributors(
    root: Path, since: str = "", author: str = ""
) -> ContributorsResult:
    """Analyze Git contributors and file churn in the given root directory.

    Args:
        root: The root directory of the Git repository.
        since: Optional time filter (e.g., '30 days ago').
        author: Optional author filter.

    Returns:
        A ContributorsResult containing the analysis.
    """
    if not (root / ".git").exists():
        return ContributorsResult([], [], [])

    contributors: list[Contributor] = []
    recent_files: list[RecentFile] = []
    churn_hotspots: list[ChurnFile] = []

    # Get contributors and commit counts
    shortlog_cmd = ["shortlog", "-sne", "--all"]
    if since:
        shortlog_cmd.extend(["--since", since])
    if author:
        shortlog_cmd.extend(["--author", author])

    shortlog_out = _run_git(shortlog_cmd, root)
    if not shortlog_out:
        return ContributorsResult([], [], [])

    for line in shortlog_out.splitlines():
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            commits = int(parts[0])
            name_email = parts[1]
            name = name_email.split(" <")[0] if " <" in name_email else name_email
            contributors.append(
                Contributor(
                    name=name,
                    commits=commits,
                    insertions=0,
                    deletions=0,
                    last_active="",
                )
            )

    # Get insertions/deletions per author
    numstat_cmd = ["log", "--format=%aN", "--numstat", "--all"]
    if since:
        numstat_cmd.extend(["--since", since])
    if author:
        numstat_cmd.extend(["--author", author])

    numstat_out = _run_git(numstat_cmd, root)
    current_author = ""
    author_stats: dict[str, dict[str, int]] = {}

    for line in numstat_out.splitlines():
        line = line.strip()
        if not line:
            continue
        if "\t" in line:
            parts = line.split("\t")
            if len(parts) >= 2 and current_author:
                ins = parts[0]
                dels = parts[1]
                if ins != "-":
                    author_stats.setdefault(current_author, {"ins": 0, "dels": 0})[
                        "ins"
                    ] += int(ins)
                if dels != "-":
                    author_stats.setdefault(current_author, {"ins": 0, "dels": 0})[
                        "dels"
                    ] += int(dels)
        else:
            current_author = line

    # Get last active date per author
    log_dates_cmd = ["log", "--format=%aN|%aI", "--all"]
    if author:
        log_dates_cmd.extend(["--author", author])

    dates_out = _run_git(log_dates_cmd, root)
    author_dates: dict[str, str] = {}
    for line in dates_out.splitlines():
        if "|" in line:
            name, date = line.split("|", 1)
            if name not in author_dates:
                author_dates[name] = date

    for c in contributors:
        stats = author_stats.get(c.name, {"ins": 0, "dels": 0})
        c.insertions = stats["ins"]
        c.deletions = stats["dels"]
        c.last_active = author_dates.get(c.name, "")

    # Recently active files (last 30 days)
    recent_cmd = ["log", "--since=30 days ago", "--name-only", "--format="]
    if author:
        recent_cmd.extend(["--author", author])

    recent_out = _run_git(recent_cmd, root)
    file_counts: dict[str, int] = {}
    for file in recent_out.splitlines():
        if file:
            file_counts[file] = file_counts.get(file, 0) + 1

    for file, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]:
        authors_out = _run_git(["log", "--format=%aN", "--follow", "--", file], root)
        unique_authors = len(set(authors_out.splitlines())) if authors_out else 0
        recent_files.append(
            RecentFile(path=file, commits=count, authors=unique_authors)
        )

    # Churn hotspots (all time)
    churn_cmd = ["log", "--name-only", "--format=", "--all"]
    churn_out = _run_git(churn_cmd, root)
    churn_counts: dict[str, int] = {}
    for file in churn_out.splitlines():
        if file:
            churn_counts[file] = churn_counts.get(file, 0) + 1

    for file, count in sorted(churn_counts.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]:
        churn_hotspots.append(ChurnFile(path=file, commits=count))

    return ContributorsResult(contributors, recent_files, churn_hotspots)
