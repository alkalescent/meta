---
title: 📦 deps
---

# 📦 deps

List dependencies parsed from the project's manifest or lockfile.

```bash
meta deps
```

```text
Production Dependencies:
click              8.3.1
typer              0.21.1
...
Development Dependencies:
pytest             9.0.2
ruff               0.14.13
...
```

Supports Node.js, Rust, Python, Go, Ruby, and PHP — detected automatically from `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `Gemfile`, or `composer.json`. Lockfiles are parsed for exact pinned versions when present, falling back to the manifest otherwise.

For `uv.lock`, the split between production and development follows the dependency graph rather than the names declared in `[dependency-groups]`. A package that reaches the tree only through a dev tool is listed as development; one reachable from both stays in production.

## Flags

| Flag | Description |
|---|---|
| `--dev` | Show only development dependencies. |
| `--outdated` | Check recorded versions against the latest available (queries npm, PyPI, or `cargo-outdated` depending on ecosystem; requires network access). |

```bash
meta deps --dev
meta deps --outdated
```

```text
Outdated:
click              8.3.1    8.4.2
pytest             9.0.2    9.1.1
```

When a project records a version range instead of a pinned version, `--outdated` reports it only if the latest release falls outside that range. A dependency declared as `typer>=0.20.1` with `0.27.1` published is up to date and is not listed.
