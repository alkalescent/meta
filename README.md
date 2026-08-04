# silicon

[![CI](https://github.com/alkalescent/silicon/actions/workflows/release.yml/badge.svg)](https://github.com/alkalescent/silicon/actions/workflows/release.yml)
[![PyPI version](https://badge.fury.io/py/silicon.svg)](https://pypi.org/project/silicon/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python CLI hello world template with best practices for packaging, testing, and CI/CD.

## ✨ Features

- **Modern CLI**: Built with [Typer](https://typer.tiangolo.com/) for a clean command-line interface
- **Well-Structured**: Source layout with `src/` directory and proper packaging
- **Comprehensive Testing**: pytest with coverage requirements and parallel execution
- **CI/CD Ready**: GitHub Actions workflows for testing, versioning, and releases
- **Multi-Platform**: PyPI, Homebrew, and pre-built binary distribution

## 💖 Support

Love this tool? Your support means the world! ❤️

<table align="center">
  <tr>
    <th>Currency</th>
    <th>Address</th>
    <th>QR</th>
  </tr>
  <tr>
    <td><strong>₿ BTC</strong></td>
    <td><code>bc1qwn7ea6s8wqx66hl5rr2supk4kv7qtcxnlqcqfk</code></td>
    <td><img src="assets/qr_btc.png" width="80" /></td>
  </tr>
  <tr>
    <td><strong>Ξ ETH</strong></td>
    <td><code>0x7cdB1861AC1B4385521a6e16dF198e7bc43fDE5f</code></td>
    <td><img src="assets/qr_eth.png" width="80" /></td>
  </tr>
  <tr>
    <td><strong>ɱ XMR</strong></td>
    <td><code>463fMSWyDrk9DVQ8QCiAir8TQd4h3aRAiDGA8CKKjknGaip7cnHGmS7bQmxSiS2aYtE9tT31Zf7dSbK1wyVARNgA9pkzVxX</code></td>
    <td><img src="assets/qr_xmr.png" width="80" /></td>
  </tr>
  <tr>
    <td><strong>◈ BNB</strong></td>
    <td><code>0x7cdB1861AC1B4385521a6e16dF198e7bc43fDE5f</code></td>
    <td><img src="assets/qr_bnb.png" width="80" /></td>
  </tr>
</table>

## 📦 Installation

### Homebrew (macOS/Linux)

```bash
brew tap alkalescent/tap
brew install silicon
```

### PyPI (Recommended)

```bash
uv pip install silicon
```

After installation, use either the command directly or as a Python module:

```bash
# Direct command
silicon --help

# As Python module (if direct command not in PATH)
uv run python -m silicon --help
```

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/alkalescent/silicon.git
cd silicon
make install DEV=1  # Install with dev dependencies
```

### Pre-built Binaries

Download from [GitHub Releases](https://github.com/alkalescent/silicon/releases):

| Variant | Description | Startup | Format |
|---------|-------------|---------|--------|
| **Portable** | Single file, no installation needed | ~10 sec | `silicon-{os}-portable` |
| **Fast** | Optimized for speed | ~1 sec | `silicon-{os}-fast.tar.gz` |

> **Note**: In the filenames and commands, replace `{os}` with your operating system (e.g., `linux`, `macos`). The examples below use `linux`. For Windows, you may need to use a tool like 7-Zip to extract `.tar.gz` archives.

For **Portable**, download and run directly:
```bash
chmod +x silicon-linux-portable
./silicon-linux-portable --help
```

For **Fast**, extract the archive and run from within:
```bash
tar -xzf silicon-linux-fast.tar.gz
./cli.dist/silicon --help
```

### Build from Source

Build your own binaries using [Nuitka](https://nuitka.net/):

```bash
git clone https://github.com/alkalescent/silicon.git
cd silicon

# Build portable (single file, slower startup)
MODE=onefile make build

# Build fast (directory, faster startup)
MODE=standalone make build
```

## 🚀 Usage

The CLI provides simple `hello` and `goodbye` commands.

### Hello Command

Say hello to someone:

```bash
silicon hello                    # Hello, World!
silicon hello --name Developer   # Hello, Developer!
silicon hello -n "Your Name"     # Hello, Your Name!
```

### Goodbye Command

Say goodbye to someone:

```bash
silicon goodbye                  # Goodbye, World!
silicon goodbye --name Developer # Goodbye, Developer!
silicon goodbye -n "Your Name"   # Goodbye, Your Name!
```

### Version

Check the installed version:

```bash
silicon version    # v1.0.0
silicon --version  # v1.0.0
silicon -v         # v1.0.0
```

## 🧪 Testing

Run the test suite:
```bash
make test
```

Run with coverage reporting (requires 90% coverage):
```bash
make cov
```

Run smoke tests:
```bash
make smoke
```

## 🏗️ Architecture

The CLI consists of the following modules:

- **`tools.py`**: Core utility classes
  - `Greeter` class: Simple greeting functionality
  
- **`cli.py`**: Command-line interface using Typer
  - `hello`: Say hello to someone
  - `goodbye`: Say goodbye to someone
  - `version`: Display version

- **`test_tools.py`** / **`test_cli.py`**: Comprehensive test suites

## 📖 Using as a Template

1. Fork or clone this repository
2. Replace `silicon` with your project name in:
   - `pyproject.toml` (name, scripts, URLs)
   - `src/silicon/` directory name
   - Imports in source files
   - README.md
3. Add your own functionality in `tools.py` and `cli.py`
4. Update tests accordingly

## 📚 Dependencies

- `typer`: Modern CLI framework

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
