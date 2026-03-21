# deps

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

## Flags

| Flag | Description |
|---|---|
| `--dev` | Show only development dependencies. |
| `--outdated` | Check installed versions against the latest available (queries npm, PyPI, or `cargo-outdated` depending on ecosystem; requires network access). |

```bash
meta deps --dev
meta deps --outdated
```

```text
Outdated:
click              8.3.1    8.4.2
pytest             9.0.2    9.1.1
```
