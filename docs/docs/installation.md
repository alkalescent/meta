---
sidebar_position: 2
---

# Installation

## Homebrew

```bash
brew tap alkalescent/tap && brew install meta
```

## PyPI

```bash
uv pip install meta.one
```

The PyPI distribution is named `meta.one`; the installed command is `meta`.

## From Source

```bash
git clone https://github.com/alkalescent/meta.git
cd meta
make install DEV=1
```

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

## Pre-built Binaries

Portable and fast standalone binaries are published on [GitHub Releases](https://github.com/alkalescent/meta/releases) for Linux, macOS, and Windows — no Python interpreter required.
