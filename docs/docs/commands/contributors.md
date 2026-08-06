---
title: 👥 contributors
---

# 👥 contributors

Summarize git contributor activity: commits, insertions, deletions, and last-active date per author, sourced from `git log`/`git shortlog`.

```bash
meta contributors
```

```text
Krish Suchak   42 commits
Alice          8 commits

Recently Active Files (last 30 days):
src/meta_one/cli.py     6 commits   2 authors
src/meta_one/deps.py    4 commits   1 authors

Churn Hotspots:
README.md               18 commits
src/meta_one/cli.py     12 commits
```

Alongside the per-author summary, the command lists the ten files touched most in the last 30 days and the ten with the highest all-time commit count.

## Flags

| Flag | Description |
|---|---|
| `--since <date>` | Only count commits since the given date (any format `git log --since` accepts, e.g. `"30 days ago"`). |
| `--author <name>` | Filter to a single author. |

```bash
meta contributors --since "30 days ago"
meta contributors --author "Krish Suchak"
```
