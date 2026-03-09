# AGENTS.md

## Overview

This repo is a Python CLI project intelligence tool (`meta`) that surfaces codebase structure, dependencies, scripts, env vars, contributors, and health. Built with Typer, packaged as `meta.one` on PyPI.

## CI Checks

All changes must pass before merging (ubuntu, macOS, Windows):

```bash
make lint      # ruff check . && ruff format --check .
make type      # ty check src tests
make cov       # pytest with coverage (90% threshold)
```

## Running Checks Locally

```bash
make ci DEV=1          # install deps (frozen lockfile, requires uv)
make lint              # lint + format check
make type              # type check (ty)
make test              # unit tests only
make cov               # unit tests with coverage
make smoke             # smoke tests (tests/smoke.py)
make format            # auto-fix lint + format
```

## Project Structure

- `src/meta_one/` - core package (detect, deps, scripts, env, size, contributors, health, output, cli)
- `tests/` - pytest unit tests and smoke tests
- `scripts/` - utility scripts (build)
- `pyproject.toml` - project config, dependencies, tool settings
- `Makefile` - build/test/lint commands

## Key Conventions

- **Package manager**: `uv` (all commands run via `uv run`)
- **Type checker**: `ty` (astral, not mypy)
- **Linter/Formatter**: `ruff`
- **Test runner**: `pytest` with `pytest-xdist` (`-n auto`) and `pytest-cov`
- **Python version**: 3.13
