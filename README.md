# meta

[![CI](https://github.com/alkalescent/meta/actions/workflows/release.yml/badge.svg)](https://github.com/alkalescent/meta/actions/workflows/release.yml)
[![PyPI version](https://badge.fury.io/py/meta.one.svg)](https://pypi.org/project/meta.one/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

meta is a minimal-dependency (runtime uses only typer), offline-first CLI that drops into any codebase and instantly surfaces what it is, how it's structured, and what you need to know. No magic, no internet required, no configuration needed.

## Installation

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

## Quick Start

```bash
meta
```
(Example output surfaces project details like structure and dependencies)

## Commands

- `deps`: List dependencies. `meta deps`
- `scripts`: List defined scripts. `meta scripts`
- `env`: List environment variables. `meta env`
- `size`: Show project size and line counts. `meta size`
- `contributors`: List top contributors. `meta contributors`
- `health`: Check project health and metrics. `meta health`

## Global Flags

| Flag | Description |
|---|---|
| `--json` | Output results in JSON format |
| `--no-color` | Disable colored output |
| `--quiet` | Suppress non-essential output |
| `--path` | Specify project path |
| `--version` | Show version |
| `--help` | Show help message |

## Testing

Run tests locally:
```bash
make test
make cov
make smoke
```

## Architecture

- `detect.py`: Project detection logic
- `deps.py`: Dependency parsing
- `scripts.py`: Script extraction
- `env.py`: Environment variable scanning
- `size.py`: Size calculation
- `contributors.py`: Git contributor analysis
- `health.py`: Health checks
- `output.py`: Output formatting
- `cli.py`: Command-line interface

## Support

<table align="center">
  <tr>
    <th>Currency</th>
    <th>Address</th>
  </tr>
  <tr>
    <td><strong>₿ BTC</strong></td>
    <td><code>bc1qwn7ea6s8wqx66hl5rr2supk4kv7qtcxnlqcqfk</code></td>
  </tr>
  <tr>
    <td><strong>Ξ ETH</strong></td>
    <td><code>0x7cdB1861AC1B4385521a6e16dF198e7bc43fDE5f</code></td>
  </tr>
  <tr>
    <td><strong>ɱ XMR</strong></td>
    <td><code>463fMSWyDrk9DVQ8QCiAir8TQd4h3aRAiDGA8CKKjknGaip7cnHGmS7bQmxSiS2aYtE9tT31Zf7dSbK1wyVARNgA9pkzVxX</code></td>
  </tr>
  <tr>
    <td><strong>◈ BNB</strong></td>
    <td><code>0x7cdB1861AC1B4385521a6e16dF198e7bc43fDE5f</code></td>
  </tr>
</table>

## License

MIT
