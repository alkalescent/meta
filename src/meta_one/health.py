"""Health check aggregation for the meta CLI tool.

Runs sub-checks and collects results for repository health.
"""

from __future__ import annotations

import datetime
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HealthCheck:
    """Represents the result of a health check."""

    status: str
    message: str


def run_health_checks(root: Path) -> list[HealthCheck]:
    """Run health checks on the given repository root.

    Args:
        root: The root directory to check.

    Returns:
        A list of HealthCheck results.
    """
    checks: list[HealthCheck] = []

    # 1. Lock file present
    lockfiles = [
        "package-lock.json",
        "yarn.lock",
        "Cargo.lock",
        "uv.lock",
        "poetry.lock",
        "Pipfile.lock",
        "go.sum",
        "Gemfile.lock",
        "composer.lock",
    ]
    if any((root / lf).exists() for lf in lockfiles):
        checks.append(HealthCheck("ok", "Lock file present"))
    else:
        checks.append(HealthCheck("warn", "No lock file found"))

    # 2. Env example present
    env_examples = [".env.example", ".env.sample", ".env.template"]
    if any((root / ee).exists() for ee in env_examples):
        checks.append(HealthCheck("ok", "Environment example file present"))
    else:
        checks.append(HealthCheck("optional", "No environment example file found"))

    # 3. Missing env vars
    try:
        from .env import analyze_env

        env_result = analyze_env(root)
        missing = [v for v in env_result.expected_vars if v.status == "MISSING"]

        if missing:
            msg = f"{len(missing)} missing required env vars"
            checks.append(HealthCheck(status="fail", message=msg))
        else:
            checks.append(
                HealthCheck(status="ok", message="No missing required env vars")
            )
    except ImportError:
        checks.append(
            HealthCheck(
                "optional",
                "Environment variable check skipped (env module not available)",
            )
        )

    # 4. Test files detected
    test_patterns = ["test_*", "*_test.*", "*.spec.*", "*.test.*"]
    test_dirs = ["src", "tests", "test", "spec", "__tests__"]
    test_found = False
    for test_dir in test_dirs:
        d = root / test_dir
        if d.exists() and d.is_dir():
            for pat in test_patterns:
                if list(d.rglob(pat)):
                    test_found = True
                    break
        if test_found:
            break

    if test_found:
        checks.append(HealthCheck("ok", "Test files detected"))
    else:
        checks.append(HealthCheck("warn", "No test files detected"))

    # 5. README freshness
    readme = root / "README.md"
    if readme.exists():
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "log", "-1", "--format=%aI", "README.md"],
                capture_output=True,
                text=True,
                check=True,
            )
            date_str = result.stdout.strip()
            if date_str:
                last_mod = datetime.datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                )
                # Naive offset-aware compare
                now = datetime.datetime.now(datetime.UTC)
                diff = now - last_mod
                if diff.days > 90:
                    checks.append(
                        HealthCheck(
                            "warn", "README.md hasn't been updated in over 90 days"
                        )
                    )
                else:
                    checks.append(HealthCheck("ok", "README.md is up to date"))
            else:
                checks.append(HealthCheck("warn", "README.md has no Git history"))
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            checks.append(HealthCheck("warn", "Could not verify README.md freshness"))
    else:
        checks.append(HealthCheck("fail", "README.md not found"))

    # 6. Gitignore present
    if (root / ".gitignore").exists():
        checks.append(HealthCheck("ok", ".gitignore present"))
    else:
        checks.append(HealthCheck("fail", ".gitignore not found"))

    # 7. No secrets in tracked files
    try:
        ls_files = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()

        secret_patterns = [
            re.compile(
                r"(api[_-]?key|apikey|api[_-]?secret)\s*[=:]\s*['\"][a-zA-Z0-9]{20,}['\"]",
                re.IGNORECASE,
            ),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            re.compile(r"(mongodb|postgres|mysql|redis)://[^\s]+:[^\s]+@"),
            re.compile(
                r"(token|secret|password)\s*[=:]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE
            ),
        ]

        secrets_found = False
        for file in ls_files:
            fpath = root / file
            if not fpath.exists() or not fpath.is_file():
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                for pattern in secret_patterns:
                    if pattern.search(content):
                        secrets_found = True
                        break
            except Exception:
                pass
            if secrets_found:
                break

        if secrets_found:
            checks.append(HealthCheck("fail", "Secrets detected in tracked files"))
        else:
            checks.append(HealthCheck("ok", "No secrets detected in tracked files"))
    except (subprocess.CalledProcessError, FileNotFoundError):
        checks.append(
            HealthCheck("optional", "Skipped secret scan (Git not available)")
        )

    # 8. CI config detected
    ci_configs = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci"]
    if any((root / ci).exists() for ci in ci_configs):
        checks.append(HealthCheck("ok", "CI configuration detected"))
    else:
        checks.append(HealthCheck("warn", "No CI configuration detected"))

    return checks
