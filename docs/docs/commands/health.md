---
title: 🩺 health
---

# 🩺 health

Run a set of repository health checks and report pass/warn/fail status for each.

```bash
meta health
```

```text
✓ Lock file present
○ No environment example file found
✓ No missing required env vars
✓ Test files detected
✓ README.md is up to date
✓ .gitignore present
✓ No secrets detected in tracked files
✓ CI configuration detected
```

Symbols are `✓` passing, `⚠` warning, `✗` failing, and `○` optional. They are colored when the terminal supports it; see [`--no-color`](../configuration.md).

## Checks

- Lock file present
- `.env.example` (or `.sample`/`.template`) present
- No missing required environment variables
- Test files detected (`test_*`, `*_test.*`, `*.spec.*`, `*.test.*`)
- README.md freshness (git history, updated within 90 days)
- `.gitignore` present
- No obvious secrets (API keys, private key headers, connection strings with embedded credentials) in tracked files. Test files are excluded, since fixture credentials there are not leaks. A hit names the file and the rule that matched.
- CI configuration detected (`.github/workflows`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci`)

CVE/vulnerability scanning of dependencies is intentionally out of scope for `health` — see [deps --outdated](./deps.md) for update checks instead.

## Flags

| Flag | Description |
|---|---|
| `--quiet` (global) | Print only failing and warning checks, omitting passing ones. |

```bash
meta --quiet health
```
