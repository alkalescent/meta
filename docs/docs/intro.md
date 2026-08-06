---
sidebar_position: 1
---

# Getting Started

**meta** is a minimal-runtime-dependency (other than [Typer](https://typer.tiangolo.com/)), offline-first CLI that drops into any codebase and instantly surfaces what it is, how it's structured, and what you need to know. No magic, no internet required, no configuration needed.

## Install

```bash
brew tap alkalescent/tap && brew install meta
```

See [Installation](./installation.md) for PyPI, source, and pre-built binary options.

## Run It

From inside any project:

```bash
meta
```

This prints a one-screen overview: project type, language breakdown, size, dependency counts, discoverable scripts, expected environment variables, git status, and a health summary.

From there, drill into any area with a subcommand — `meta deps`, `meta scripts`, `meta env`, `meta size`, `meta contributors`, or `meta health`. Each one is documented under [Commands](./commands/overview.md).

## Global Flags

Every command accepts the same global flags — `--json` for machine-readable output, `--quiet` for a condensed summary, `--path` to target a different directory, and more. See [Configuration](./configuration.md) for the full list.
