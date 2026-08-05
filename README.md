# meta

[![CI](https://github.com/alkalescent/meta/actions/workflows/release.yml/badge.svg)](https://github.com/alkalescent/meta/actions/workflows/release.yml)
[![PyPI version](https://badge.fury.io/py/meta.one.svg)](https://pypi.org/project/meta.one/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

meta is a minimal-dependency (runtime uses only typer), offline-first CLI that drops into any codebase and instantly surfaces what it is, how it's structured, and what you need to know. No magic, no internet required, no configuration needed.

## ✨ Features

- **Instant Detection**: Project type, framework, and language from marker files — no configuration needed
- **Dependency Visibility**: Production and dev dependencies across Node.js, Python, Rust, Go, Ruby, and PHP
- **Script Discovery**: Runnable scripts from package.json, Makefile, justfile, Taskfile.yml, and pyproject.toml
- **Environment Awareness**: Expected vs. set environment variables, with source usage locations
- **Health Checks**: Missing lockfiles, stale READMEs, leaked secrets, missing CI config
- **Multi-Platform**: PyPI, Homebrew, and pre-built binary distribution

## 📦 Installation

### Homebrew
```bash
brew tap alkalescent/tap && brew install meta
```

### PyPI
```bash
uv pip install meta.one
```

### From Source
```bash
git clone https://github.com/alkalescent/meta.git
cd meta
make install DEV=1
```

### Pre-built Binaries
Download from GitHub Releases for portable or fast execution options.

## 🚀 Quick Start

```bash
meta
```
(Example output surfaces project details like structure and dependencies)

## 🛠️ Commands

- `deps`: List dependencies. `meta deps`
- `scripts`: List defined scripts. `meta scripts`
- `env`: List environment variables. `meta env`
- `size`: Show project size and line counts. `meta size`
- `contributors`: List top contributors. `meta contributors`
- `health`: Check project health and metrics. `meta health`

## ⚙️ Global Flags

| Flag | Description |
|---|---|
| `--json` | Output results in JSON format |
| `--no-color` | Disable colored output |
| `--quiet` | Suppress non-essential output |
| `--path` | Specify project path |
| `--version` | Show version |
| `--help` | Show help message |

## 🧪 Testing

Run tests locally:
```bash
make test
make cov
make smoke
```

## 🏗️ Architecture

- `detect.py`: Project detection logic
- `deps.py`: Dependency parsing
- `scripts.py`: Script extraction
- `env.py`: Environment variable scanning
- `size.py`: Size calculation
- `contributors.py`: Git contributor analysis
- `health.py`: Health checks
- `output.py`: Output formatting
- `cli.py`: Command-line interface

## 📄 License

MIT
