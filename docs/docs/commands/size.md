---
title: 📏 size
---

# 📏 size

Analyze codebase size: file and line counts by language, by directory, and the largest individual files. Respects `.gitignore` via `git ls-files` when run inside a git repository.

```bash
meta size
```

```text
Total: 43 files, 23800 lines, 847322 bytes

Languages:
Python      23  2955   12.4%
JSON        3   19528  82.0%
...

Directories:
src               11  2224
tests             11  622
...

Largest Files:
src/meta_one/cli.py   431
...
```

## Flags

| Flag | Description |
|---|---|
| `--sort <lines\|files\|bytes>` | Sort language and directory breakdowns by total lines, file count, or byte size. Defaults to `lines`. |
| `--depth <n>` | Maximum directory depth to aggregate into the directory breakdown. Defaults to `3`. |
| `--code-only` | Exclude blank lines and comment lines from line counts. |

```bash
meta size --sort bytes --depth 2
```
